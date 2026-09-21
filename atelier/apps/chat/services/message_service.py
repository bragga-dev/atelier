"""
Message Service — enviar mensagem (texto e/ou anexos) e marcar como lida.

Ponto único de entrada tanto pro consumer do WebSocket (mensagem só-texto,
enviada ao vivo) quanto pro endpoint REST de upload (mensagem com anexo,
que precisa de multipart — WebSocket não é o canal certo pra isso). Os
dois caminhos terminam aqui, e daqui sai o broadcast pro grupo — assim
quem está com o chat aberto recebe a mensagem na hora, não importa por
qual canal ela entrou.
"""
from typing import List, Optional
from uuid import UUID

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

from atelier.apps.accounts.selectors.user_selector import get_user_by_id
from atelier.apps.chat.repositories.conversation_repository import touch_last_message
from atelier.apps.chat.repositories.message_repository import (
    add_attachment,
    create_message,
    mark_conversation_messages_as_read,
)
from atelier.apps.chat.schemas.chat_schema import MessageOut
from atelier.apps.chat.selectors.conversation_selector import (
    get_conversation_by_id,
    user_can_access_conversation,
)
from atelier.apps.chat.selectors.message_selector import get_messages_for_conversation
from atelier.apps.core.exceptions import (
    ConversationNotFound,
    EmptyMessage,
    PermissionDenied,
    TooManyAttachments,
    UserNotFound,
)
from atelier.apps.core.validators.chat_attachment_validator import get_attachment_type

from atelier.apps.chat.repositories.message_repository import mark_messages_as_read
from atelier.apps.chat.selectors.message_selector import get_unread_messages_for_reader



MAX_ATTACHMENTS_PER_MESSAGE = 5


def _group_name(conversation_id: UUID) -> str:
    return f"chat_{conversation_id}"


def broadcast_message(message_out: MessageOut) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        _group_name(message_out.conversation_id),
        {"type": "chat.message", "message": message_out.model_dump(mode="json")},
    )


def _ensure_participant(conversation, user):
    if not user_can_access_conversation(conversation, user):
        raise PermissionDenied("Você não pode enviar mensagens nesta conversa.")


@transaction.atomic
def send_message(
    *,
    conversation_id: UUID,
    sender_id: UUID,
    content: str = "",
    files: Optional[List] = None,
) -> MessageOut:
    conversation = get_conversation_by_id(conversation_id)
    if conversation is None:
        raise ConversationNotFound()

    sender = get_user_by_id(user_id=sender_id)
    if sender is None:
        raise UserNotFound()

    _ensure_participant(conversation, sender)

    files = files or []
    content = (content or "").strip()

    if not content and not files:
        raise EmptyMessage()
    if len(files) > MAX_ATTACHMENTS_PER_MESSAGE:
        raise TooManyAttachments()

    message = create_message(conversation=conversation, sender=sender, content=content)

    for uploaded_file in files:
        add_attachment(
            message=message,
            file=uploaded_file,
            file_type=get_attachment_type(uploaded_file.name),
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
        )

    touch_last_message(conversation)

    message.refresh_from_db()
    message_out = MessageOut.from_orm(message)

    transaction.on_commit(lambda: broadcast_message(message_out))

    return message_out


def list_messages(*, user_id: UUID, conversation_id: UUID) -> List[MessageOut]:
    conversation = get_conversation_by_id(conversation_id)
    if conversation is None:
        raise ConversationNotFound()

    user = get_user_by_id(user_id=user_id)
    if user is None:
        raise UserNotFound()
    _ensure_participant(conversation, user)

    messages = get_messages_for_conversation(conversation_id)
    return [MessageOut.from_orm(m) for m in messages]



def mark_conversation_as_read(*, user_id: UUID, conversation_id: UUID) -> int:
    conversation = get_conversation_by_id(conversation_id)
    if conversation is None:
        raise ConversationNotFound()

    user = get_user_by_id(user_id=user_id)
    if user is None:
        raise UserNotFound()
    _ensure_participant(conversation, user)

    unread = get_unread_messages_for_reader(conversation_id, user_id)
    updated = mark_messages_as_read(unread)

    if updated:
        channel_layer = get_channel_layer()
        if channel_layer is not None:
            async_to_sync(channel_layer.group_send)(
                _group_name(conversation_id),
                {"type": "chat.read", "reader_id": str(user_id)},
            )
    return updated
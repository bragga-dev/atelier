from typing import Iterable

from django.utils import timezone

from atelier.apps.accounts.models.user_model import User
from atelier.apps.chat.models.conversation_model import Conversation
from atelier.apps.chat.models.message_attachment_model import MessageAttachment
from atelier.apps.chat.models.message_model import Message


def create_message(conversation: Conversation, sender: User, content: str = "") -> Message:
    message = Message(conversation=conversation, sender=sender, content=content)
    message.full_clean()
    message.save()
    return message


def add_attachment(message: Message, *, file, file_type: str, original_filename: str, file_size: int) -> MessageAttachment:
    attachment = MessageAttachment(
        message=message,
        file=file,
        file_type=file_type,
        original_filename=original_filename,
        file_size=file_size,
    )
    attachment.full_clean()
    attachment.save()
    return attachment


def mark_conversation_messages_as_read(conversation_id, reader_id) -> int:
    """Marca como lidas as mensagens da conversa que NÃO foram enviadas pelo próprio leitor."""
    return (
        Message.objects.filter(conversation_id=conversation_id, is_read=False)
        .exclude(sender_id=reader_id)
        .update(is_read=True, read_at=timezone.now())
    )
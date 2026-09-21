from django.utils import timezone

from atelier.apps.accounts.models.user_model import User
from atelier.apps.chat.models.conversation_model import Conversation
from atelier.apps.payments.models.order_model import Order


def get_or_create_conversation(client: User, order: Order | None = None) -> tuple[Conversation, bool]:
    """
    Um cliente tem no máximo 1 conversa aberta "geral" por vez; se `order`
    for informado, a conversa é específica daquele pedido (permite ter uma
    conversa geral + uma por pedido em paralelo, sem misturar assunto).
    """
    return Conversation.objects.get_or_create(
        client=client,
        order=order,
        status=Conversation.Status.OPEN,
        defaults={"subject": f"Pedido {order.code}" if order else ""},
    )


def close_conversation(conversation: Conversation) -> Conversation:
    conversation.status = Conversation.Status.CLOSED
    conversation.save(update_fields=["status"])
    return conversation


def touch_last_message(conversation: Conversation, when=None) -> None:
    conversation.last_message_at = when or timezone.now()
    conversation.save(update_fields=["last_message_at"])
"""
Tasks Celery — envio do e-mail de confirmação de recebimento do pedido
(disparado logo após o checkout, antes até de o cliente escolher a forma
de pagamento).
"""
import logging
import uuid

from celery import shared_task

from atelier.apps.accounts.selectors.user_selector import get_user_by_id
from atelier.apps.core.emails.sender import send_html_email
from atelier.apps.payments.emails.payment_context import (
    build_order_summary_block,
    client_orders_url,
    store_url,
)
from atelier.apps.payments.selectors.order_selector import get_order_by_id
from atelier.apps.products.emails.product_context import (
    build_order_datetime_block,
    resolve_client_display_name,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_received(self, user_id: uuid.UUID, order_id: uuid.UUID) -> None:
    """Confirma pro cliente que o pedido foi recebido e aguarda pagamento."""
    user = get_user_by_id(user_id=user_id)
    order = get_order_by_id(order_id=order_id)

    if user is None or order is None:
        logger.error(
            "Não foi possível enviar e-mail de pedido recebido: user ou order "
            "inexistente (user=%s, order=%s). Task não será reagendada.",
            user_id, order_id,
        )
        return

    try:
        context = {
            "client_name": resolve_client_display_name(user),
            "user_email": user.email,

            **build_order_summary_block(order),
            **build_order_datetime_block(order),

            "client_orders_url": client_orders_url(),
            "store_url": store_url(),
        }

        send_html_email(
            subject=f"Recebemos seu pedido {order.code} — SOL E ARTE",
            to_email=user.email,
            template_name="payment/emails/order_received.html",
            context=context,
        )

        logger.info("Order received email sent to %s (order=%s)", user.email, order.order_id)

    except Exception as exc:
        logger.exception("Error sending order received email (user=%s, order=%s)", user_id, order_id)
        raise self.retry(exc=exc)
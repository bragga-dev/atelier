"""
Tasks Celery — envio do e-mail de cancelamento de pedido (disparado quando
o próprio cliente cancela um pedido pendente).
"""
import logging
import uuid

from celery import shared_task

from atelier.apps.core.emails.sender import send_html_email
from atelier.apps.payments.emails.payment_context import (
    build_order_summary_block,
    client_orders_url,
    store_url,
)
from atelier.apps.payments.selectors.order_selector import get_order_by_id
from atelier.apps.products.emails.product_context import (
    build_order_datetime_block,
    new_order_url,
    resolve_client_display_name,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_cancelled(self, order_id: uuid.UUID) -> None:
    """Confirma pro cliente que o pedido foi cancelado."""
    order = get_order_by_id(order_id=order_id)
    if order is None:
        logger.error(
            "Não foi possível enviar e-mail de pedido cancelado: order "
            "inexistente (order=%s). Task não será reagendada.",
            order_id,
        )
        return

    user = order.user_id
    try:
        context = {
            "client_name": resolve_client_display_name(user),
            "user_email": user.email,
            "order_canceled_reason": order.canceled_reason,

            **build_order_summary_block(order),
            **build_order_datetime_block(order),

            "client_orders_url": client_orders_url(),
            "store_url": store_url(),
            "new_order_url": new_order_url(),
        }

        send_html_email(
            subject=f"Pedido {order.code} cancelado — ÉLUXO MODAS",
            to_email=user.email,
            template_name="payment/emails/order_cancelled.html",
            context=context,
        )

        logger.info("Order cancelled email sent to %s (order=%s)", user.email, order.order_id)

    except Exception as exc:
        logger.exception("Error sending order cancelled email (order=%s)", order_id)
        raise self.retry(exc=exc)
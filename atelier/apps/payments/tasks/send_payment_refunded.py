"""
Tasks Celery — envio do e-mail de estorno (disparado quando o webhook da
Asaas confirma o reembolso do pagamento).
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
    resolve_client_display_name,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_refunded(self, order_id: uuid.UUID) -> None:
    """Avisa o cliente que o pagamento do pedido foi estornado."""
    order = get_order_by_id(order_id=order_id)
    if order is None:
        logger.error(
            "Não foi possível enviar e-mail de estorno: order inexistente "
            "(order=%s). Task não será reagendada.",
            order_id,
        )
        return

    user = order.user_id
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
            subject=f"Pagamento estornado — pedido {order.code} — SOL E ARTE",
            to_email=user.email,
            template_name="payment/emails/payment_refunded.html",
            context=context,
        )

        logger.info("Payment refunded email sent to %s (order=%s)", user.email, order.order_id)

    except Exception as exc:
        logger.exception("Error sending payment refunded email (order=%s)", order_id)
        raise self.retry(exc=exc)
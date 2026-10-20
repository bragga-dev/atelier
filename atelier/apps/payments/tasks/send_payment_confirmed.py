"""
Tasks Celery — envio do e-mail de confirmação de pagamento (disparado
quando o webhook da Asaas marca o pedido como COMPLETED).
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
def send_payment_confirmed(self, order_id: uuid.UUID) -> None:
    """Avisa o cliente que o pagamento do pedido foi confirmado."""
    order = get_order_by_id(order_id=order_id)
    if order is None:
        logger.error(
            "Não foi possível enviar e-mail de pagamento confirmado: order "
            "inexistente (order=%s). Task não será reagendada.",
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
            subject=f"Pagamento confirmado — pedido {order.code} — SOL E ARTE",
            to_email=user.email,
            template_name="payment/emails/payment_confirmed.html",
            context=context,
        )

        logger.info("Payment confirmed email sent to %s (order=%s)", user.email, order.order_id)

    except Exception as exc:
        logger.exception("Error sending payment confirmed email (order=%s)", order_id)
        raise self.retry(exc=exc)
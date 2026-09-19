"""
Helpers privados de montagem de contexto para os e-mails de pagamento..
"""

from django.conf import settings


from atelier.apps.core.permissions.roles import is_client
from atelier.apps.payments.models.order_model import Order
from atelier.apps.payments.models.payment_model import Payment
from atelier.apps.payments.models.asaas_customer_model import AsaasCustomer

_CLIENT_ORDER_PATH = "/painel/meus-pedidos"
_STORE_PATH = "/"

def build_frontend_url(path: str) -> str:
    """Monta uma URL absoluta do frontend a partir de um path relativo."""
    return f"{settings.FRONTEND_URL}{path}"


def client_orders_url() -> str:
    """Link para a área 'Meus pedidos' do cliente."""
    return build_frontend_url(_CLIENT_ORDER_PATH)

def store_url() -> str:
    """Link para a página da loja."""
    return build_frontend_url(_STORE_PATH)


def build_order_summary_block(order: Order) -> dict:
    """
    Resumo do pedido (itens + valores) — usado nos e-mails de ciclo de vida
    do pedido (recebido, pagamento confirmado, cancelado, estornado).
    Espera que `order.items` já venha prefetchado (ver `get_order_by_id`).
    """
    items = [
        {
            "name": item.product_id.product_name,
            "quantity": item.order_item_quantity,
            "unit_price": item.order_item_price,
            "subtotal": item.subtotal(),
        }
        for item in order.items.all()
    ]
    return {
        "order_code": order.code,
        "order_items": items,
        "order_subtotal": order.subtotal,
        "order_shipping_total": order.order_shipping_total,
        "order_total": order.total_geral,
    }


def build_payment_block(payment: Payment, customer: AsaasCustomer) -> dict:
    """Campos praticados no momento do pagamento."""
    return {
        "code_payment": payment.asaas_payment_id or payment.payment_id,
        "payment_description": payment.description,
        "payment_value": payment.value,
        "payment_order": payment.order_id,
        "payment_asaas_customer_id": customer.asaas_customer_id,
        "payment_asaas_id": payment.asaas_payment_id,
        "payment_billing_type": payment.billing_type,
        "payment_due_date": payment.due_date,
        "payment_invoice_url": payment.invoice_url,
        "payment_pix_qr_code": f"data:image/png;base64,{payment.pix_qr_code}" if payment.pix_qr_code else None,
        "payment_created_at": payment.created_at,
        "payment_pix_copy_paste": payment.pix_copy_paste,    
        
    }
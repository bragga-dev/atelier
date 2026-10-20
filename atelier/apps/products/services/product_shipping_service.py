"""
ProductShipping Services — orquestra os dados físicos (peso/dimensões) de
um produto usados na cotação de frete.
"""
import uuid
from typing import Optional

from atelier.apps.core.exceptions.products_exception import (
    ProductNotFound,
    ShippingAlreadyExists,
    ShippingNotFound,
)
from atelier.apps.core.utils.fields import drop_none
from atelier.apps.products.repositories.product_shipping_repository import (
    create_shipping,
    delete_shipping,
    update_shipping,
)
from atelier.apps.products.schemas.product_shipping_schema import (
    ShippingCreateIn,
    ShippingOut,
    ShippingUpdateIn,
)
from atelier.apps.products.selectors.product_shipping_selector import (
    get_shipping_by_product,
    shipping_exists_for_product,
)
from atelier.apps.products.selectors.product_selector import get_product_by_id


def _get_shipping_or_raise(product_id: uuid.UUID):
    shipping = get_shipping_by_product(product_id)
    if shipping is None:
        raise ShippingNotFound()
    return shipping


# ── Leitura ──────────────────────────────────────────────────────────────

def get_shipping_for_all(product_id: uuid.UUID) -> ShippingOut:
    shipping = _get_shipping_or_raise(product_id)
    return ShippingOut.from_orm(shipping)


def get_shipping_payload(product_id: uuid.UUID, quantity: Optional[int] = None) -> dict:
    """
    Monta o payload pronto para a API de frete (ex.: Melhor Envio) a
    partir dos dados cadastrados do produto.

    `quantity` sobrescreve a quantidade padrão de embalagem quando o
    chamador já sabe quantas unidades vão no carrinho/pedido — é isso
    que deve ser usado no checkout, não o valor default do cadastro.
    """
    shipping = _get_shipping_or_raise(product_id)
    payload = shipping.to_shipping_payload()
    if quantity is not None:
        payload["quantity"] = quantity
    return payload


# ── Escrita ──────────────────────────────────────────────────────────────

def create_shipping_for_admin(product_id: uuid.UUID, data: ShippingCreateIn) -> ShippingOut:
    product = get_product_by_id(product_id)
    if product is None:
        raise ProductNotFound()

    if shipping_exists_for_product(product_id):
        raise ShippingAlreadyExists()

    shipping = create_shipping(
        product_id=product,
        weight=data.weight,
        height=data.height,
        width=data.width,
        length=data.length,
        quantity=data.quantity,
    )
    return ShippingOut.from_orm(shipping)


def update_shipping_for_admin(product_id: uuid.UUID, data: ShippingUpdateIn) -> ShippingOut:
    shipping = _get_shipping_or_raise(product_id)
    shipping = update_shipping(shipping, **drop_none(data.dict(exclude_unset=True)))
    return ShippingOut.from_orm(shipping)


def delete_shipping_for_admin(product_id: uuid.UUID) -> None:
    shipping = _get_shipping_or_raise(product_id)
    delete_shipping(shipping)
"""
CartItem Repository — persistência pura de CartItem. Nenhuma regra de
negócio nem consulta aqui (validação de estoque, decisão de criar vs.
incrementar, recálculo dos totais do Cart, busca de itens, etc.) — isso é
responsabilidade exclusiva do service (e dos selectors). O repository só
executa a operação de persistência que já foi decidida e validada antes.
"""
from django.db.models import QuerySet

from atelier.apps.cart.models.cart_item_model import CartItem
from atelier.apps.cart.models.cart_model import Cart
from atelier.apps.products.models.product_model import Product


def create_item(cart: Cart, product: Product, quantity: int = 1) -> CartItem:
    item = CartItem(cart_id=cart, product_id=product, quantity_item=quantity)
    item.save()
    return item


def update_item_quantity(item: CartItem, quantity: int) -> CartItem:
    """Define a quantidade exata (não soma)."""
    item.quantity_item = quantity
    item.save(update_fields=["quantity_item"])
    return item


def remove_item(item: CartItem) -> None:
    item.delete()


def delete_items(items: QuerySet[CartItem]) -> None:
    items.delete()


def set_item_shipping(item: CartItem, shipping_type: str, shipping_value) -> CartItem:
    item.shipping_type = shipping_type
    item.shipping_value = shipping_value
    item.save(update_fields=["shipping_type", "shipping_value"])
    return item
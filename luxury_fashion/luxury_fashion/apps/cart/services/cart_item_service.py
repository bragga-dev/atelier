"""
CartItem Service — orquestra regras de negócio de itens do carrinho
(repositories + selectors), devolvendo sempre schemas prontos para a
camada de API.
"""
import uuid

from luxury_fashion.apps.cart.repositories.cart_item_repository import (
    create_item,
    increment_item_quantity,
    remove_item,
    update_item_quantity,
)
from luxury_fashion.apps.cart.services.cart_service import get_or_create_cart_for_user
from luxury_fashion.apps.cart.schemas.cart_item_schema import CartItemCreateIn
from luxury_fashion.apps.cart.schemas.cart_schema import CartOut
from luxury_fashion.apps.cart.selectors.cart_item_selector import (
    get_item_by_id_and_cart,
    get_item_by_product,
)
from luxury_fashion.apps.cart.selectors.cart_selector import get_cart_by_user_id
from luxury_fashion.apps.core.exceptions.cart_exception import CartItemNotFound, InsufficientStock
from luxury_fashion.apps.core.exceptions.products_exception import ProductNotFound
from luxury_fashion.apps.products.selectors.product_selector import get_product_by_id


def _get_cart_item_or_raise(cart_item_id: uuid.UUID, cart_id: uuid.UUID):
    item = get_item_by_id_and_cart(cart_item_id=cart_item_id, cart_id=cart_id)
    if item is None:
        raise CartItemNotFound()
    return item


def _cart_out_for(user_id: uuid.UUID) -> CartOut:
    cart = get_cart_by_user_id(user_id)
    return CartOut.from_orm(cart)


def add_item_to_cart(user_id: uuid.UUID, data: CartItemCreateIn) -> CartOut:
    cart = get_or_create_cart_for_user(user_id=user_id)

    product = get_product_by_id(product_id=data.product_id)
    if product is None:
        raise ProductNotFound()

    existing = get_item_by_product(cart_id=cart.cart_id, product_id=product.product_id)
    new_quantity = (existing.quantity_item if existing else 0) + data.quantity_item

    if new_quantity > product.stock:
        raise InsufficientStock()

    if existing:
        increment_item_quantity(item=existing, quantity=data.quantity_item)
    else:
        create_item(cart=cart, product=product, quantity=data.quantity_item)

    return _cart_out_for(user_id=user_id)


def update_cart_item_quantity(user_id: uuid.UUID, cart_item_id: uuid.UUID, quantity: int) -> CartOut:
    cart = get_or_create_cart_for_user(user_id=user_id)
    item = _get_cart_item_or_raise(cart_item_id=cart_item_id, cart_id=cart.cart_id)

    if quantity > item.product_id.stock:
        raise InsufficientStock()

    update_item_quantity(item=item, quantity=quantity)
    return _cart_out_for(user_id=user_id)


def remove_item_from_cart(user_id: uuid.UUID, cart_item_id: uuid.UUID) -> CartOut:
    cart = get_or_create_cart_for_user(user_id=user_id)
    item = _get_cart_item_or_raise(cart_item_id=cart_item_id, cart_id=cart.cart_id)

    remove_item(item)
    return _cart_out_for(user_id=user_id)
from uuid import UUID
from atelier.apps.accounts.models.user_model import User
from atelier.apps.cart.models.cart_model import Cart
from atelier.apps.cart.repositories.cart_item_repository import delete_items
from atelier.apps.cart.repositories.cart_repository import create_cart
from atelier.apps.cart.schemas.cart_schema import CartOut
from atelier.apps.cart.selectors.cart_item_selector import get_items_by_cart
from atelier.apps.cart.selectors.cart_selector import get_cart_by_user_id
from atelier.apps.accounts.selectors.user_selector import get_user_by_id
from atelier.apps.core.exceptions.user import UserNotFound


def get_or_create_cart_for_user(user_id: UUID) -> Cart:
    cart = get_cart_by_user_id(user_id=user_id)
    if cart is not None:
        return cart

    user = get_user_by_id(user_id=user_id)
    if user is None:
        raise UserNotFound()
    return create_cart(user)

def get_cart_for_client(user_id: UUID) -> CartOut:
    get_or_create_cart_for_user(user_id=user_id)
    cart = get_cart_by_user_id(user_id=user_id)
    return CartOut.from_orm(cart)


def clear_cart_for_client(user_id: UUID) -> CartOut:
    cart = get_or_create_cart_for_user(user_id=user_id)
    delete_items(get_items_by_cart(cart_id=cart.cart_id))
    cart.update_totals()
    return get_cart_for_client(user_id=user_id)
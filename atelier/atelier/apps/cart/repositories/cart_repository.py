
from atelier.apps.accounts.models.user_model import User
from atelier.apps.cart.models.cart_model import Cart


def create_cart(user: User) -> Cart:
    cart = Cart(user_id=user)
    cart.full_clean()
    cart.save()
    return cart
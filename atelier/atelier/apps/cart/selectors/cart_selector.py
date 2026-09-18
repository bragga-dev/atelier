"""
Cart Selectors — queries de leitura. Nenhuma escrita acontece aqui.
"""
import uuid
from typing import Optional

from django.db.models import Prefetch, QuerySet

from atelier.apps.cart.models.cart_item_model import CartItem
from atelier.apps.cart.models.cart_model import Cart


def _with_items(qs: QuerySet[Cart]) -> QuerySet[Cart]:
    items_qs = CartItem.objects.select_related("product_id").prefetch_related("product_id__categories", "product_id__images")
    return qs.prefetch_related(Prefetch("items", queryset=items_qs))


def get_cart_by_user_id(user_id: uuid.UUID) -> Optional[Cart]:
    return _with_items(Cart.objects).filter(user_id=user_id).first()


def get_cart_by_id(cart_id: uuid.UUID) -> Optional[Cart]:
    return _with_items(Cart.objects).filter(cart_id=cart_id).first()


def cart_has_items(cart_id: uuid.UUID) -> bool:
    return CartItem.objects.filter(cart_id=cart_id).exists()
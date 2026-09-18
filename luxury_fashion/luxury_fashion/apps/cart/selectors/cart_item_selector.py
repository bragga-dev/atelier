"""
CartItem Selectors — queries de leitura. Nenhuma escrita acontece aqui.
"""
from uuid import UUID
from typing import Optional

from django.db.models import QuerySet

from luxury_fashion.apps.cart.models.cart_item_model import CartItem


def get_item_by_id(cart_item_id: UUID) -> Optional[CartItem]:
    return (CartItem.objects.select_related("product_id").prefetch_related("product_id__categories", "product_id__images").filter(cart_item_id=cart_item_id).first())


def get_item_by_id_and_cart(cart_item_id: UUID, cart_id: UUID) -> Optional[CartItem]:
    return (CartItem.objects.select_related("product_id").prefetch_related("product_id__categories", "product_id__images").filter(cart_item_id=cart_item_id, cart_id=cart_id).first())


def get_item_by_product(cart_id: UUID, product_id: UUID) -> Optional[CartItem]:
    return CartItem.objects.filter(cart_id=cart_id, product_id=product_id).first()


def get_items_by_cart(cart_id: UUID) -> QuerySet[CartItem]:
    return CartItem.objects.filter(cart_id=cart_id).select_related("product_id").prefetch_related("product_id__categories", "product_id__images")
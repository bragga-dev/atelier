"""
ProductShipping Selectors — queries de leitura. Nenhuma escrita acontece aqui.
"""
import uuid
from typing import Optional

from luxury_fashion.apps.products.models.product_shipping_model import ProductShipping


def get_shipping_by_product(product_id: uuid.UUID) -> Optional[ProductShipping]:
    return ProductShipping.objects.select_related("product_id").filter(product_id=product_id).first()


def shipping_exists_for_product(product_id: uuid.UUID) -> bool:
    return ProductShipping.objects.filter(product_id=product_id).exists()
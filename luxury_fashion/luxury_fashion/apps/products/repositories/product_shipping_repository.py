"""
ProductShipping Repository — persistência dos dados de frete (peso/dimensões)
de um Product.
"""
from decimal import Decimal
from typing import Optional

from luxury_fashion.apps.products.models.product_shipping_model import ProductShipping
from luxury_fashion.apps.products.models.product_model import Product


def create_shipping(
    product_id: Product,
    weight: Decimal,
    height: Decimal,
    width: Decimal,
    length: Decimal,
    quantity: int = 1,
) -> ProductShipping:
    shipping = ProductShipping(
        product_id=product_id,
        weight=weight,
        height=height,
        width=width,
        length=length,
        quantity=quantity,
    )
    shipping.full_clean()
    shipping.save()
    return shipping


def update_shipping(shipping: ProductShipping, **fields) -> ProductShipping:
    for attr, value in fields.items():
        if value is not None:
            setattr(shipping, attr, value)
    shipping.full_clean()
    shipping.save()
    return shipping


def delete_shipping(shipping: ProductShipping) -> None:
    shipping.delete()


def get_or_create_shipping(product_id: Product, **defaults) -> tuple[ProductShipping, bool]:
    """
    Útil no formulário de cadastro de produto: garante que sempre exista
    um registro de frete associado, mesmo que criado vazio/zerado a princípio.
    """
    shipping, created = ProductShipping.objects.get_or_create(
        product_id=product_id,
        defaults=defaults,
    )
    return shipping, created
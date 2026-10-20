"""
ProductShipping Repository — persistência dos dados de frete (peso/dimensões)
de um Product.
"""
from decimal import Decimal

from atelier.apps.products.models.product_shipping_model import ProductShipping
from atelier.apps.products.models.product_model import Product


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
        setattr(shipping, attr, value)
    shipping.full_clean()
    shipping.save()
    return shipping


def delete_shipping(shipping: ProductShipping) -> None:
    shipping.delete()
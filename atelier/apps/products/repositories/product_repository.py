"""
Product Repository — persistência de Product.

Este módulo só deve conter acesso a dados (criar/ler/atualizar/excluir no
banco). Qualquer decisão sobre *quais* campos aplicar, *se* uma transição de
estado é permitida, mensagens de erro de domínio etc. é regra de negócio e
pertence ao service.
"""
from decimal import Decimal
from typing import Iterable, Optional

from atelier.apps.products.models.product_category_model import ProductCategory
from atelier.apps.products.models.product_model import Product


def create_product(
    product_name: str,
    categories: Iterable[ProductCategory],
    price: Decimal,
    stock: int = 0,
    description: str = "",
    is_active: bool = True,
) -> Product:
    product = Product(
        product_name=product_name,
        price=price,
        stock=stock,
        description=description,
        is_active=is_active,
    )
    product.full_clean(exclude=["categories"])
    product.save()
    product.categories.set(categories)
    return product


def update_product(product: Product, categories: Optional[Iterable[ProductCategory]] = None, **fields) -> Product:
    """
    Aplica no model exatamente os campos recebidos. A decisão de quais
    campos entram aqui (ex.: só os explicitamente enviados, se `None` deve
    ou não limpar um campo, etc.) é responsabilidade do service — o
    repository apenas persiste o que já chegou pronto.

    `categories`, por ser M2M, é aplicado à parte via `.set()`.
    """
    for attr, value in fields.items():
        setattr(product, attr, value)
    product.full_clean(exclude=["categories"])
    product.save()
    if categories is not None:
        product.categories.set(categories)
    return product


def delete_product(product: Product) -> None:
    product.delete()


def activate_product(product: Product) -> Product:
    product.is_active = True
    product.save(update_fields=["is_active"])
    return product


def deactivate_product(product: Product) -> Product:
    product.is_active = False
    product.save(update_fields=["is_active"])
    return product


def set_product_stock(product: Product, stock: int) -> Product:
    product.stock = stock
    product.full_clean(exclude=["categories"])
    product.save(update_fields=["stock"])
    return product
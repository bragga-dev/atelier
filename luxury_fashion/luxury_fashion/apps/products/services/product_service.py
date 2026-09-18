"""
Product Services — orquestra regras de negócio de produtos
(repositories + selectors), devolvendo sempre schemas prontos
para a camada de API.
"""
import uuid
from typing import Optional

from django.db import transaction

from luxury_fashion.apps.core.exceptions.cart_exception import InsufficientStock
from luxury_fashion.apps.core.exceptions.products_exception import (
    CategoryNotFound,
    ProductNameAlreadyExists,
    ProductNotFound,
)
from luxury_fashion.apps.products.repositories.product_repository import (
    activate_product,
    adjust_product_stock,
    create_product,
    deactivate_product,
    delete_product,
    set_product_stock,
    update_product,
)
from luxury_fashion.apps.products.schemas.product_schema import (
    ProductCreateFullIn,
    ProductCreateIn,
    ProductListOut,
    ProductOut,
    ProductUpdateIn,
)
from luxury_fashion.apps.products.selectors.product_category_selector import get_category_by_id
from luxury_fashion.apps.products.selectors.product_selector import (
    filter_products,
    get_all_products,
    get_product_by_id,
    product_name_exists,
)


def _get_product_or_raise(product_id: uuid.UUID):
    product = get_product_by_id(product_id)
    if product is None:
        raise ProductNotFound()
    return product


def _get_categories_or_raise(category_ids):
    categories = []
    for category_id in category_ids:
        category = get_category_by_id(product_category_id=category_id)
        if category is None:
            raise CategoryNotFound()
        categories.append(category)
    return categories


# ── Leitura ──────────────────────────────────────────────────────────────

def get_product_for_all(product_id: uuid.UUID) -> ProductOut:
    product = _get_product_or_raise(product_id=product_id)
    return ProductOut.from_orm(product)


def list_products_for_all(active_only: bool = True) -> list[ProductListOut]:
    products = get_all_products(active_only=active_only)
    return [ProductListOut.from_orm(product) for product in products]


def search_products_for_all(
    search: Optional[str] = None,
    product_category_id: Optional[uuid.UUID] = None,
    in_stock_only: bool = False,
    active_only: bool = True,
) -> list[ProductListOut]:
    """Filtro combinado da vitrine — usado pela busca/listagem pública."""
    products = filter_products(
        search=search,
        product_category_id=product_category_id,
        in_stock_only=in_stock_only,
        active_only=active_only,
    )
    return [ProductListOut.from_orm(product) for product in products]


def search_products_queryset(
    search: Optional[str] = None,
    product_category_id: Optional[uuid.UUID] = None,
    in_stock_only: bool = False,
    active_only: bool = True,
    sort: Optional[str] = None,
):
    """
    Mesma filtragem de `search_products_for_all`, mas devolve o QuerySet
    bruto (sem serializar) para paginação na camada de router.
    """
    return filter_products(
        search=search,
        product_category_id=product_category_id,
        in_stock_only=in_stock_only,
        active_only=active_only,
        sort=sort,
    )


# ── Escrita ──────────────────────────────────────────────────────────────

def create_product_for_amdin(data: ProductCreateIn) -> ProductOut:
    categories = _get_categories_or_raise(data.category_ids)

    if product_name_exists(data.product_name):
        raise ProductNameAlreadyExists()

    product = create_product(
        product_name=data.product_name,
        categories=categories,
        price=data.price,
        stock=data.stock,
        description=data.description,
    )
    return get_product_for_all(product_id=product.product_id)


def create_product_full_for_admin(
    data: ProductCreateFullIn,
    images: Optional[list] = None,
    cover_index: int = 0,
) -> ProductOut:

    from luxury_fashion.apps.products.services.product_image_service import (
        upload_image_for_admin,
    )
    from luxury_fashion.apps.products.services.product_shipping_service import (
        create_shipping_for_admin,
    )

    images = images or []

    with transaction.atomic():
        product = create_product_for_amdin(
            ProductCreateIn(
                product_name=data.product_name,
                category_ids=data.category_ids,
                price=data.price,
                stock=data.stock,
                description=data.description,
            )
        )
        create_shipping_for_admin(product_id=product.product_id, data=data.shipping)

        for index, image_file in enumerate(images):
            upload_image_for_admin(
                product.product_id,
                image_file,
                is_cover=(index == cover_index),
                display_order=index,
            )

    return get_product_for_all(product_id=product.product_id)


def update_product_for_admin(product_id: uuid.UUID, data: ProductUpdateIn) -> ProductOut:
    product = _get_product_or_raise(product_id=product_id)

    if data.product_name is not None and product_name_exists(product_name=data.product_name, exclude_id=product_id):
        raise ProductNameAlreadyExists()

    payload = data.dict(exclude_unset=True)
    categories = None
    if "category_ids" in payload:
        category_ids = payload.pop("category_ids")
        categories = _get_categories_or_raise(category_ids) if category_ids is not None else None

    fields = {key: value for key, value in payload.items() if value is not None}

    product = update_product(product=product, categories=categories, **fields)
    return get_product_for_all(product_id=product.product_id)


def delete_product_for_admin(product_id: uuid.UUID) -> None:
    product = _get_product_or_raise(product_id=product_id)
    delete_product(product=product)


def activate_product_for_admin(product_id: uuid.UUID) -> ProductOut:
    product = _get_product_or_raise(product_id=product_id)
    product = activate_product(product=product)
    return ProductOut.from_orm(product)


def deactivate_product_for_admin(product_id: uuid.UUID) -> ProductOut:
    product = _get_product_or_raise(product_id=product_id)
    product = deactivate_product(product=product)
    return ProductOut.from_orm(product)


def adjust_product_stock_for_admin(product_id: uuid.UUID, delta: int) -> ProductOut:
    product = _get_product_or_raise(product_id=product_id)
    if product.stock + delta < 0:
        raise InsufficientStock()
    product = adjust_product_stock(product=product, delta=delta)
    return ProductOut.from_orm(product)


def set_product_stock_for_admin(product_id: uuid.UUID, stock: int) -> ProductOut:
    product = _get_product_or_raise(product_id=product_id)
    if stock < 0:
        raise InsufficientStock()
    product = set_product_stock(product=product, stock=stock)
    return ProductOut.from_orm(product)
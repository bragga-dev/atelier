"""
Product Selectors — queries de leitura. Nenhuma escrita acontece aqui.
"""
import uuid
from typing import Optional

from django.db.models import Prefetch, Q, QuerySet

from luxury_fashion.apps.products.models.product_category_model import ProductCategory
from luxury_fashion.apps.products.models.product_image_model import ProductImage
from luxury_fashion.apps.products.models.product_model import Product


def _with_categories_and_images(qs: QuerySet[Product]) -> QuerySet[Product]:
    """
    Prefetch de `categories` e `images` (capa primeiro, depois
    display_order) — evita N+1 quando a listagem serializa categorias e a
    imagem de capa de cada produto.
    """
    return qs.prefetch_related(
        "categories",
        Prefetch("images", queryset=ProductImage.objects.order_by("-is_cover", "display_order", "created_at")),
    )


def get_product_by_id(product_id: uuid.UUID) -> Optional[Product]:
    qs = Product.objects.prefetch_related("categories", "images")
    return qs.filter(product_id=product_id).first()


def product_name_exists(product_name: str, exclude_id: Optional[uuid.UUID] = None) -> bool:
    qs = Product.objects.filter(product_name__iexact=product_name)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return qs.exists()


def get_all_products(active_only: bool = True) -> QuerySet[Product]:
    qs = Product.objects.all()
    if active_only:
        qs = qs.filter(is_active=True)
    return _with_categories_and_images(qs)


def filter_products(
    search: Optional[str] = None,
    product_category_id: Optional[uuid.UUID] = None,
    in_stock_only: bool = False,
    active_only: bool = True,
    sort: Optional[str] = None,
) -> QuerySet[Product]:
    """
    Filtro combinado da vitrine.

    `sort`: None (default) mantém a ordenação alfabética de `Product.Meta`
    (usada no catálogo/busca). `"recent"` ordena pelos mais recém-criados
    primeiro — usado na seção "Novidades" da home.
    """
    qs = Product.objects.all()

    if active_only:
        qs = qs.filter(is_active=True)

    if search:
        search = search.strip()
        qs = qs.filter(
            Q(product_name__icontains=search)
            | Q(categories__category_name__icontains=search)
        )

    if product_category_id:
        qs = qs.filter(categories__product_category_id=product_category_id)

    if in_stock_only:
        qs = qs.filter(stock__gt=0)

    qs = qs.distinct()
    if sort == "recent":
        qs = qs.order_by("-created_at")

    return _with_categories_and_images(qs)
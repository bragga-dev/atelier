import uuid
from decimal import Decimal
from typing import List, Optional

from ninja import Schema
from pydantic import field_validator

from luxury_fashion.apps.products.models.product_model import Product
from luxury_fashion.apps.products.schemas.produc_image_schema import ImageOut
from luxury_fashion.apps.products.schemas.product_category_schema import ProductCategoryOut
from luxury_fashion.apps.products.schemas.product_shipping_schema import ShippingCreateIn


def _pick_cover_image(images: list) -> Optional["ImageOut"]:
    """Capa explícita (`is_cover=True`); na ausência, a primeira por display_order."""
    if not images:
        return None
    cover = next((img for img in images if img.is_cover), None)
    return ImageOut.from_orm(cover or images[0])


class ProductCreateIn(Schema):
    product_name: str
    category_ids: List[uuid.UUID]
    price: Decimal
    stock: int = 0
    description: str = ""

    @field_validator("product_name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome não pode ser vazio.")
        return v

    @field_validator("category_ids")
    @classmethod
    def at_least_one_category(cls, v: List[uuid.UUID]) -> List[uuid.UUID]:
        if not v:
            raise ValueError("O produto precisa pertencer a pelo menos uma categoria.")
        return v

    @field_validator("price")
    @classmethod
    def price_not_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Preço não pode ser negativo.")
        return v


class ProductCreateFullIn(Schema):
    """
    Payload de conveniência para o formulário de cadastro completo: cria o
    produto (com preço/estoque/descrição/categorias) e os dados de frete
    (peso/dimensões) numa única chamada.

    As tabelas continuam normalizadas (Product / ProductShipping) — este
    schema só agrupa a entrada para o front não precisar orquestrar 2
    requisições.
    """
    product_name: str
    category_ids: List[uuid.UUID]
    price: Decimal
    stock: int = 0
    description: str = ""
    shipping: ShippingCreateIn

    @field_validator("product_name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome não pode ser vazio.")
        return v

    @field_validator("category_ids")
    @classmethod
    def at_least_one_category(cls, v: List[uuid.UUID]) -> List[uuid.UUID]:
        if not v:
            raise ValueError("O produto precisa pertencer a pelo menos uma categoria.")
        return v

    @field_validator("price")
    @classmethod
    def price_not_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Preço não pode ser negativo.")
        return v


class ProductUpdateIn(Schema):
    product_name: Optional[str] = None
    category_ids: Optional[List[uuid.UUID]] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProductListOut(Schema):
    """
    Versão da vitrine/listagem: inclui preço, estoque, categorias e a
    imagem de capa. Não carrega a galeria completa — para isso use o
    endpoint de detalhe (`ProductOut`).
    """
    product_id: uuid.UUID
    product_name: str
    categories: List[ProductCategoryOut]
    is_active: bool
    price: Decimal
    stock: int
    description: str
    in_stock: bool
    cover_image: Optional[ImageOut] = None

    @classmethod
    def from_orm(cls, product: Product) -> "ProductListOut":
        # `product.categories`/`product.images` já vêm prefetchadas pelo
        # selector — usar `.all()` aproveita o cache do prefetch em vez de
        # disparar uma query nova por produto.
        images = list(product.images.all())
        categories = [ProductCategoryOut.from_orm(c) for c in product.categories.all()]

        return cls(
            product_id=product.product_id,
            product_name=product.product_name,
            categories=categories,
            is_active=product.is_active,
            price=product.price,
            stock=product.stock,
            description=product.description,
            in_stock=product.in_stock,
            cover_image=_pick_cover_image(images),
        )


class ProductOut(ProductListOut):
    """Versão completa — usada na página de detalhe (com galeria de imagens)."""
    images: List[ImageOut] = []
    created_at: str
    updated_at: str

    @classmethod
    def from_orm(cls, product: Product) -> "ProductOut":
        images = list(product.images.all())
        categories = [ProductCategoryOut.from_orm(c) for c in product.categories.all()]

        return cls(
            product_id=product.product_id,
            product_name=product.product_name,
            categories=categories,
            is_active=product.is_active,
            price=product.price,
            stock=product.stock,
            description=product.description,
            in_stock=product.in_stock,
            images=[ImageOut.from_orm(img) for img in images],
            cover_image=_pick_cover_image(images),
            created_at=product.created_at.isoformat(),
            updated_at=product.updated_at.isoformat(),
        )
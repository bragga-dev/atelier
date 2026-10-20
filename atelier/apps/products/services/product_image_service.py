"""
ProductImage Services — orquestra regras de negócio de imagens de
produto (repositories + selectors), devolvendo sempre schemas prontos
para a camada de API.
"""
import uuid
from typing import Optional

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from ninja import UploadedFile

from atelier.apps.core.exceptions.media import InvalidImageFile
from atelier.apps.core.exceptions.products_exception import ImageNotFound, ProductNotFound
from atelier.apps.core.tasks.media import delete_old_media_file
from atelier.apps.core.utils.fields import drop_none
from atelier.apps.core.validators.image_validator import validate_image_file
from atelier.apps.products.repositories.product_image_repository import (
    create_image, 
    delete_image, 
    reorder_image, 
    set_cover_image, 
    unset_cover_image, 
    update_image, 
)
from atelier.apps.products.schemas.produc_image_schema import ImageOut, ImageUpdateIn
from atelier.apps.products.selectors.product_image_selector import (
    get_cover_image,
    get_image_by_id,
    get_images_by_product,
)
from atelier.apps.products.selectors.product_selector import get_product_by_id


def _get_image_or_raise(image_id: uuid.UUID):
    image = get_image_by_id(image_id)
    if image is None:
        raise ImageNotFound()
    return image


def _unset_current_cover(product_id: uuid.UUID, exclude_image_id: Optional[uuid.UUID] = None) -> None:
    """Regra: só existe uma capa por produto — desmarca a capa atual antes de promover outra."""
    current_cover = get_cover_image(product_id)
    if current_cover is not None and current_cover.pk != exclude_image_id:
        unset_cover_image(current_cover)


# ── Leitura ──────────────────────────────────────────────────────────────

def get_image_for_all(image_id: uuid.UUID) -> ImageOut:
    image = _get_image_or_raise(image_id)
    return ImageOut.from_orm(image)


def list_images_for_all(product_id: uuid.UUID) -> list[ImageOut]:
    images = get_images_by_product(product_id)
    return [ImageOut.from_orm(image) for image in images]


def list_images_queryset(product_id: uuid.UUID):
    """QuerySet bruto de imagens do produto, para paginação na camada de router."""
    return get_images_by_product(product_id)


# ── Escrita ──────────────────────────────────────────────────────────────

@transaction.atomic
def upload_image_for_admin(
    product_id: uuid.UUID,
    image: UploadedFile,
    is_cover: bool = False,
    display_order: int = 0,
) -> ImageOut:
    product = get_product_by_id(product_id)
    if product is None:
        raise ProductNotFound()

    try:
        validate_image_file(image)
    except DjangoValidationError as exc:
        raise InvalidImageFile(exc.messages[0] if getattr(exc, "messages", None) else str(exc))

    if is_cover:
        _unset_current_cover(product_id=product.product_id)

    created = create_image(
        product_id=product,
        product_image=image,
        is_cover=is_cover,
        display_order=display_order,
    )
    return ImageOut.from_orm(created)


def update_image_for_admin(image_id: uuid.UUID, data: ImageUpdateIn) -> ImageOut:
    image = _get_image_or_raise(image_id)
    image = update_image(image, **drop_none(data.dict(exclude_unset=True)))
    return ImageOut.from_orm(image)


def delete_image_for_admin(image_id: uuid.UUID) -> None:
    image = _get_image_or_raise(image_id)
    old_name = image.product_image.name if image.product_image else None
    delete_image(image)
    if old_name:
        delete_old_media_file.delay(old_name)


@transaction.atomic
def set_cover_image_for_admin(image_id: uuid.UUID) -> ImageOut:
    image = _get_image_or_raise(image_id)
    _unset_current_cover(product_id=image.product_id_id, exclude_image_id=image.pk)
    image = set_cover_image(image)
    return ImageOut.from_orm(image)


def reorder_image_for_admin(image_id: uuid.UUID, display_order: int) -> ImageOut:
    image = _get_image_or_raise(image_id)
    image = reorder_image(image, display_order)
    return ImageOut.from_orm(image)
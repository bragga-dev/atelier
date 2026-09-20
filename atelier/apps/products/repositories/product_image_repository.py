"""
ProductImage Repository — persistência de ProductImage.
"""
from django.core.files import File
from django.db import transaction

from atelier.apps.products.models.product_image_model import ProductImage
from atelier.apps.products.models.product_model import Product

@transaction.atomic
def create_image(
    product_id: Product,
    product_image: File,
    is_cover: bool = False,
    display_order: int = 0,
) -> ProductImage:
    image = ProductImage(
        product_id=product_id,
        product_image=product_image,
        is_cover=is_cover,
        display_order=display_order,
    )
    image.full_clean()
    image.save()
    return image


def update_image(image: ProductImage, **fields) -> ProductImage:
    for attr, value in fields.items():
        setattr(image, attr, value)
    image.full_clean()
    image.save()
    return image


def delete_image(image: ProductImage) -> None:
    image.delete()


@transaction.atomic
def set_cover_image(image: ProductImage) -> ProductImage:
    """
    Marca `image` como capa do produto. Desmarcar a capa atual (se existir) é decisão do service.
    """
    image.is_cover = True
    image.save(update_fields=["is_cover"])
    return image


def unset_cover_image(image: ProductImage) -> ProductImage:
    image.is_cover = False
    image.save(update_fields=["is_cover"])
    return image


def reorder_image(image: ProductImage, display_order: int) -> ProductImage:
    image.display_order = display_order
    image.save(update_fields=["display_order"])
    return image
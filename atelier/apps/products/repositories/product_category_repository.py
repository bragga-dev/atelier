"""
ProductCategory Repository — persistência de ProductCategory.
"""
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from atelier.apps.products.models.product_category_model import ProductCategory


def create_category(
    category_name: str,
    **fields,
) -> ProductCategory:
    category = ProductCategory(category_name=category_name, **fields)
    category.full_clean()
    category.save()
    return category


def update_category(category: ProductCategory, **fields) -> ProductCategory:
    for attr, value in fields.items():
        setattr(category, attr, value)
    category.full_clean()
    category.save()
    return category


def delete_category(category: ProductCategory) -> None:
    category.delete()


def activate_category(category: ProductCategory) -> ProductCategory:
    category.is_active = True
    category.save(update_fields=["is_active"])
    return category


def deactivate_category(category: ProductCategory) -> ProductCategory:
    category.is_active = False
    category.save(update_fields=["is_active"])
    return category


def set_category_image(category: ProductCategory, image: File) -> ProductCategory:
    category.category_image = image
    category.full_clean()
    category.save(update_fields=["category_image"])
    return category


def remove_category_image(category: ProductCategory) -> ProductCategory:
    category.category_image = "default/category_img.jpg"
    category.save(update_fields=["category_image"])
    return category
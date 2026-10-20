"""
Admin Repository — persistência do perfil do Administrador.
"""
from django.core.files.uploadedfile import InMemoryUploadedFile

from atelier.apps.accounts.models.user_model import User
from atelier.apps.accounts.models.admin_model import AdminProfile, DEFAULT_ADMIN_PHOTO


def create_admin_profile(
    user_id: User,
    full_name: str,
    **fields,
) -> AdminProfile:
    admin_profile = AdminProfile(user_id=user_id, full_name=full_name, **fields)
    admin_profile.save()
    return admin_profile


def update_admin_profile(admin_profile: AdminProfile, **fields) -> AdminProfile:
    for attr, value in fields.items():
        setattr(admin_profile, attr, value)
    admin_profile.save()
    return admin_profile


def delete_admin_profile(admin_profile: AdminProfile) -> None:
    admin_profile.delete()


def set_admin_photo(admin_profile: AdminProfile, photo: InMemoryUploadedFile) -> AdminProfile:
    admin_profile.photo = photo
    admin_profile.save(update_fields=["photo"])
    return admin_profile


def remove_admin_photo(admin_profile: AdminProfile) -> AdminProfile:
    admin_profile.photo = DEFAULT_ADMIN_PHOTO
    admin_profile.save(update_fields=["photo"])
    return admin_profile
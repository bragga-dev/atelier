"""
Admin Profile Services — atualização do perfil (nome completo + foto)
do usuário ADMIN logado.
"""
import uuid
from typing import Optional

from ninja import UploadedFile
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files import File

from atelier.apps.accounts.models.admin_model import AdminProfile, DEFAULT_ADMIN_PHOTO
from atelier.apps.accounts.models.user_model import User
from atelier.apps.accounts.repositories.admin_repository import (
    create_admin_profile as create_admin_profile_repo,
    set_admin_photo,
    remove_admin_photo,
    update_admin_profile as update_admin_profile_repo,
)
from atelier.apps.accounts.schemas.admin_schema import AdminProfileOut, AdminProfileUpdateIn
from atelier.apps.accounts.selectors.admin_selector import get_admin_profile_by_user_id
from atelier.apps.accounts.selectors.user_selector import get_user_with_related
from atelier.apps.core.exceptions.user import UserNotFound
from atelier.apps.core.exceptions.permissions import PermissionDenied
from atelier.apps.core.exceptions.media import InvalidImageFile
from atelier.apps.core.tasks.media import delete_old_media_file
from atelier.apps.core.utils.fields import drop_none
from atelier.apps.core.validators.image_validator import validate_image_file


def create_admin_profile(user_id: User, full_name: str, photo: Optional[File] = None) -> AdminProfile:
    fields = {"full_name": full_name}
    if photo is not None:
        fields["photo"] = photo

    return create_admin_profile_repo(user_id=user_id, **fields)


def update_admin_profile(user_id: uuid.UUID, payload: AdminProfileUpdateIn) -> AdminProfileOut:
    user = get_user_with_related(user_id)
    if not user:
        raise UserNotFound("Usuário não encontrado.")

    if user.role != User.UserRole.ADMIN:
        raise PermissionDenied("Apenas administradores podem atualizar este perfil.")

    admin_profile = getattr(user, "admin_profile", None)
    if not admin_profile:
        raise UserNotFound("Perfil de administrador não encontrado.")

    fields = drop_none(payload.dict(exclude_unset=True))
    updated = update_admin_profile_repo(admin_profile=admin_profile, **fields)
    return AdminProfileOut.from_orm(updated)


def upload_admin_profile_photo(user_id: uuid.UUID, photo: UploadedFile) -> AdminProfileOut:
    admin_profile = get_admin_profile_by_user_id(user_id=user_id)
    if not admin_profile:
        raise UserNotFound("Perfil de administrador não encontrado.")

    try:
        validate_image_file(photo)
    except DjangoValidationError as e:
        raise InvalidImageFile(e.messages[0] if getattr(e, "messages", None) else str(e))

    old_name = admin_profile.photo.name if admin_profile.photo and admin_profile.photo.name != DEFAULT_ADMIN_PHOTO else None
    updated = set_admin_photo(admin_profile=admin_profile, photo=photo)
    if old_name:
        delete_old_media_file.delay(old_name)
    return AdminProfileOut.from_orm(updated)


def delete_admin_profile_photo(user_id: uuid.UUID) -> AdminProfileOut:
    admin_profile = get_admin_profile_by_user_id(user_id=user_id)
    if not admin_profile:
        raise UserNotFound("Perfil de administrador não encontrado.")

    old_name = admin_profile.photo.name if admin_profile.photo and admin_profile.photo.name != DEFAULT_ADMIN_PHOTO else None
    updated = remove_admin_photo(admin_profile=admin_profile)
    if old_name:
        delete_old_media_file.delay(old_name)
    return AdminProfileOut.from_orm(updated)
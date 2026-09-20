import uuid
from ninja import UploadedFile
from django.core.exceptions import ValidationError as DjangoValidationError
from atelier.apps.core.tasks.media import delete_old_media_file
from atelier.apps.core.validators.image_validator import validate_image_file
from atelier.apps.accounts.models.client_model import DEFAULT_CLIENT_PHOTO
from atelier.apps.accounts.repositories.client_repository import set_client_photo, remove_client_photo
from atelier.apps.accounts.schemas.client_schema import ClientOut
from atelier.apps.accounts.selectors.client_selector import get_client_by_user_id
from atelier.apps.core.exceptions.user import UserNotFound
from atelier.apps.core.exceptions.permissions import PermissionDenied
from atelier.apps.accounts.models.user_model import User
from atelier.apps.core.exceptions.media import InvalidImageFile

def upload_client_profile_photo(user_id: User, photo: UploadedFile) -> ClientOut:
   
    client = get_client_by_user_id(user_id=user_id)
    if not client:
        raise UserNotFound("Cliente não encontrado.")

    try:
        validate_image_file(photo)
    except DjangoValidationError as e:
        raise InvalidImageFile(e.messages[0] if getattr(e, "messages", None) else str(e))

    old_name = client.photo.name if client.photo and client.photo.name != DEFAULT_CLIENT_PHOTO else None
    updated_client = set_client_photo(client=client, photo=photo)
    if old_name:
        delete_old_media_file.delay(old_name)
    return ClientOut.from_orm(updated_client)


def delete_client_profile_photo(user_id: User) -> ClientOut:
 
    client = get_client_by_user_id(user_id=user_id)
    if not client:
        raise UserNotFound("Cliente não encontrado.")

    old_name = client.photo.name if client.photo and client.photo.name != DEFAULT_CLIENT_PHOTO else None
    updated_client = remove_client_photo(client=client)
    if old_name:
        delete_old_media_file.delay(old_name)
    return ClientOut.from_orm(updated_client)
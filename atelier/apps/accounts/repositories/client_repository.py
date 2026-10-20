"""
Client Repository — persistência de perfil Membro.
"""
from atelier.apps.accounts.models.user_model import User
from atelier.apps.accounts.models.client_model import Client
from django.core.files.uploadedfile import InMemoryUploadedFile


def create_client(
    user_id: User,
    **fields,
) -> Client:
    client = Client(user_id=user_id, **fields)
    client.save()
    return client




def update_client(client: Client, **fields) -> Client:
    for attr, value in fields.items():
        setattr(client, attr, value)
    client.full_clean()   
    client.save()
    return client


def delete_client(client: Client) -> None:
    client.delete()




def set_client_photo(client: Client, photo: InMemoryUploadedFile) -> Client:
    client.photo = photo
    client.save(update_fields=["photo"])
    return client


def remove_client_photo(client: Client) -> Client:
    client.photo = "default/client_img.jpg"
    client.save(update_fields=["photo"])
    return client
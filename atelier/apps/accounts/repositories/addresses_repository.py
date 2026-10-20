from atelier.apps.accounts.models.addresses_client_model import AddressesClient
from atelier.apps.accounts.models.client_model import Client


def create_address(
    client_id: Client,
    **fields,
) -> AddressesClient:
    address = AddressesClient(client_id=client_id, **fields)
    address.full_clean()
    address.save()
    return address




def update_address(address: AddressesClient, **fields) -> AddressesClient:
    for attr, value in fields.items():
        setattr(address, attr, value)
    address.full_clean()   
    address.save()
    return address


def delete_address(address: AddressesClient) -> None:
    address.delete()


def update_status_address_up(address: AddressesClient) -> AddressesClient:
    address.is_preferential = True
    address.save(update_fields=["is_preferential"])
    return address


def update_status_address_down(address: AddressesClient) -> AddressesClient:
    address.is_preferential = False
    address.save(update_fields=["is_preferential"])
    return address
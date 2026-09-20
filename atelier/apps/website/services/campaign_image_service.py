"""
CampaignImage Services — orquestra regras de negócio de imagens/banners
de campanha (repositories + selectors), devolvendo sempre schemas
prontos para a camada de API.
"""

import uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from ninja import UploadedFile

from atelier.apps.core.exceptions.campaign_exception import (
    CampaignImageNotFound,
    CampaignNotFound,
)
from atelier.apps.core.exceptions.media import InvalidImageFile
from atelier.apps.core.tasks.media import delete_old_media_file
from atelier.apps.core.validators.image_validator import validate_image_file

from atelier.apps.website.models.campaignImage_model import CampaignImage

from atelier.apps.website.repositories.campaign_image_repository import (
    create_campaign_image,
    delete_campaign_image,
    reorder_campaign_image,
    set_cover_campaign_image,
    unset_cover_campaign_image,
    update_campaign_image,
)

from atelier.apps.website.schemas.campaign_image_schema import (
    CampaignImageOut,
    CampaignImageUpdateIn,
)

from atelier.apps.website.selectors.campaign_image_selector import (
    get_campaign_image_by_id,
    get_cover_image as get_campaign_cover_image,
    get_images_by_campaign,
)

from atelier.apps.website.selectors.campaign_selector import (
    get_campaign_by_id,
)


def _get_campaign_image_or_raise(
    campaign_image_id: uuid.UUID,
) -> CampaignImage:

    campaign_image = get_campaign_image_by_id(campaign_image_id)

    if campaign_image is None:
        raise CampaignImageNotFound()

    return campaign_image


@transaction.atomic
def _promote_campaign_image_to_cover(
    campaign_image: CampaignImage,
) -> CampaignImage:

    # Regra de negócio:
    # só existe uma capa por campanha; a capa atual
    # é desmarcada antes de promover a nova.
    current_cover = get_campaign_cover_image(
        campaign_image.campaign_id_id,
    )

    if current_cover is not None and current_cover.pk != campaign_image.pk:
        unset_cover_campaign_image(current_cover)

    return set_cover_campaign_image(campaign_image)


# ── Leitura ──────────────────────────────────────────────────────────────

def get_campaign_image_for_all(
    campaign_image_id: uuid.UUID,
) -> CampaignImageOut:

    campaign_image = _get_campaign_image_or_raise(campaign_image_id)

    return CampaignImageOut.from_orm(campaign_image)


def list_campaign_images_for_all(
    campaign_id: uuid.UUID,
) -> list[CampaignImageOut]:

    images = get_images_by_campaign(campaign_id)

    return [
        CampaignImageOut.from_orm(image)
        for image in images
    ]


# ── Escrita ──────────────────────────────────────────────────────────────

def upload_campaign_image_for_admin(
    campaign_id: uuid.UUID,
    image: UploadedFile,
    is_cover: bool = False,
    display_order: int = 0,
) -> CampaignImageOut:

    campaign = get_campaign_by_id(campaign_id)

    if campaign is None:
        raise CampaignNotFound()

    try:
        validate_image_file(image)
    except DjangoValidationError as exc:
        raise InvalidImageFile(
            exc.messages[0]
            if getattr(exc, "messages", None)
            else str(exc)
        )

    # Regra de negócio:
    # uma nova imagem marcada como capa deve remover
    # a capa atualmente existente.
    if is_cover:
        set_cover = True
    else:
        set_cover = False

    created = create_campaign_image(
        campaign=campaign,
        image=image,
        is_cover=False,
        display_order=display_order,
    )

    if set_cover:
        created = _promote_campaign_image_to_cover(created)

    return CampaignImageOut.from_orm(created)


def update_campaign_image_for_admin(
    campaign_image_id: uuid.UUID,
    data: CampaignImageUpdateIn,
) -> CampaignImageOut:

    campaign_image = _get_campaign_image_or_raise(campaign_image_id)

    fields = data.dict(exclude_unset=True)

    campaign_image = update_campaign_image(
        campaign_image,
        **fields,
    )

    return CampaignImageOut.from_orm(campaign_image)


def delete_campaign_image_for_admin(
    campaign_image_id: uuid.UUID,
) -> None:

    campaign_image = _get_campaign_image_or_raise(
        campaign_image_id,
    )

    old_name = campaign_image.image.name if campaign_image.image else None

    delete_campaign_image(campaign_image)

    if old_name:
        delete_old_media_file.delay(old_name)


def set_cover_campaign_image_for_admin(
    campaign_image_id: uuid.UUID,
) -> CampaignImageOut:

    campaign_image = _get_campaign_image_or_raise(
        campaign_image_id,
    )

    # Regra de negócio:
    # se já é a capa, não há nada a fazer.
    if not campaign_image.is_cover:
        campaign_image = _promote_campaign_image_to_cover(
            campaign_image,
        )

    return CampaignImageOut.from_orm(campaign_image)


def reorder_campaign_image_for_admin(
    campaign_image_id: uuid.UUID,
    display_order: int,
) -> CampaignImageOut:

    campaign_image = _get_campaign_image_or_raise(
        campaign_image_id,
    )

    campaign_image = reorder_campaign_image(
        campaign_image,
        display_order,
    )

    return CampaignImageOut.from_orm(campaign_image)
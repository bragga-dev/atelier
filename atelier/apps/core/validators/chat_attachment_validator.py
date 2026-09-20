import os

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from ninja import UploadedFile
from PIL import Image, UnidentifiedImageError

# =========================================================
# VALIDAÇÃO DE ANEXO DE CHAT (foto, vídeo, PDF, TXT)
# =========================================================
# Diferente de `validate_image_file` (produtos), aqui aceitamos vários
# tipos de arquivo num único campo, então a extensão decide qual conjunto
# de regras aplicar. Vídeo/PDF/TXT são validados só por extensão + tamanho
# (não temos uma lib de sniff de conteúdo tipo `python-magic` no projeto);
# imagem reaproveita a verificação real do Pillow, que já existe.

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}
DOCUMENT_EXTENSIONS = {".pdf", ".txt"}

ALL_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | DOCUMENT_EXTENSIONS

MAX_IMAGE_SIZE_MB = 5
MAX_VIDEO_SIZE_MB = 50
MAX_DOCUMENT_SIZE_MB = 10

VALID_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


class ChatAttachmentType:
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


def get_attachment_type(filename: str) -> str:
    ext = os.path.splitext(filename)[-1].lower()
    if ext in IMAGE_EXTENSIONS:
        return ChatAttachmentType.IMAGE
    if ext in VIDEO_EXTENSIONS:
        return ChatAttachmentType.VIDEO
    if ext in DOCUMENT_EXTENSIONS:
        return ChatAttachmentType.DOCUMENT
    raise ValidationError(
        _("Extensão '%(ext)s' não suportada. Use: %(valid)s."),
        params={"ext": ext, "valid": ", ".join(sorted(ALL_EXTENSIONS))},
    )


def validate_chat_attachment_file(value) -> None:
    if not isinstance(value, UploadedFile):
        return

    attachment_type = get_attachment_type(value.name)

    if attachment_type == ChatAttachmentType.IMAGE:
        _validate_image(value)
    elif attachment_type == ChatAttachmentType.VIDEO:
        _validate_size(value, MAX_VIDEO_SIZE_MB)
    else:
        _validate_size(value, MAX_DOCUMENT_SIZE_MB)


def _validate_size(value, max_mb: int) -> None:
    if value.size > max_mb * 1024 * 1024:
        raise ValidationError(
            _("O arquivo (%(size).1f MB) excede o limite de %(max)s MB."),
            params={"size": value.size / (1024 * 1024), "max": max_mb},
        )


def _validate_image(value) -> None:
    _validate_size(value, MAX_IMAGE_SIZE_MB)
    try:
        value.seek(0)
        img = Image.open(value)
        img.verify()
        value.seek(0)
        img = Image.open(value)
        if (img.format or "").upper() not in VALID_IMAGE_FORMATS:
            raise ValidationError(
                _("Formato de imagem '%(fmt)s' não suportado."), params={"fmt": img.format}
            )
    except UnidentifiedImageError:
        raise ValidationError(_("O arquivo não é uma imagem reconhecida."))
    except ValidationError:
        raise
    except Exception:
        raise ValidationError(_("Arquivo de imagem inválido ou corrompido."))
    finally:
        value.seek(0)
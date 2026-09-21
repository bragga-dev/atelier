"""
Chat API — abrir conversa, listar, enviar mensagem (com anexo) e marcar
como lida. O envio de texto "ao vivo" acontece pelo WebSocket
(`ws/chat/<conversation_id>/`, ver `consumers.py`); esta rota de envio
aqui é a usada quando a mensagem tem anexo (upload multipart), mas também
aceita mensagem só-texto sem problema.
"""
from typing import List, Optional
from uuid import UUID

from django_ratelimit.decorators import ratelimit
from ninja import File, Form, Router, UploadedFile

from atelier.apps.accounts.models.user_model import User
from atelier.apps.core.exceptions import (
    ConversationNotFound,
    EmptyMessage,
    PermissionDenied,
    TooManyAttachments,
)
from atelier.apps.core.permissions.auth_classes import AdminOnlyAuth, AllRolesAuth
from atelier.apps.core.schemas.deafult_schema import MessageOut as ErrorOut
from atelier.apps.chat.schemas.chat_schema import (
    ConversationOut,
    MessageOut,
    StartConversationIn,
)
from atelier.apps.chat.services.conversation_service import (
    get_conversation_for_user,
    list_conversations_for_admin,
    list_conversations_for_client,
    start_or_resume_conversation,
)
from atelier.apps.chat.services.message_service import (
    list_messages,
    mark_conversation_as_read,
    send_message,
)

router = Router()


# ═══════════════════════════════════════════════════════════════════════════════
# Conversas
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/conversations",
    response={201: ConversationOut},
    auth=AllRolesAuth(),
    summary="Abre uma conversa (ou retoma a já aberta) com a loja",
)
@ratelimit(key="user", rate="10/m", block=True)
def start_conversation_router(request, payload: StartConversationIn):
    user: User = request.auth
    return 201, start_or_resume_conversation(client_user_id=user.user_id, order_id=payload.order_id)


@router.get(
    "/conversations/mine",
    response={200: List[ConversationOut]},
    auth=AllRolesAuth(),
    summary="Cliente lista as próprias conversas",
)
@ratelimit(key="user", rate="30/m", block=True)
def list_my_conversations_router(request):
    user: User = request.auth
    return 200, list_conversations_for_client(client_user_id=user.user_id)


@router.get(
    "/conversations/admin",
    response={200: List[ConversationOut]},
    auth=AdminOnlyAuth(),
    summary="Admin lista todas as conversas (inbox)",
)
@ratelimit(key="user", rate="30/m", block=True)
def list_all_conversations_router(request, status: Optional[str] = None):
    return 200, list_conversations_for_admin(status=status)


@router.get(
    "/conversations/{conversation_id}",
    response={200: ConversationOut, 403: ErrorOut, 404: ErrorOut},
    auth=AllRolesAuth(),
    summary="Detalhe de uma conversa",
)
@ratelimit(key="user", rate="30/m", block=True)
def get_conversation_router(request, conversation_id: UUID):
    user: User = request.auth
    try:
        return 200, get_conversation_for_user(user_id=user.user_id, conversation_id=conversation_id)
    except ConversationNotFound as e:
        return 404, {"detail": str(e)}
    except PermissionDenied as e:
        return 403, {"detail": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# Mensagens
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/conversations/{conversation_id}/messages",
    response={200: List[MessageOut], 403: ErrorOut, 404: ErrorOut},
    auth=AllRolesAuth(),
    summary="Lista o histórico de mensagens da conversa",
)
@ratelimit(key="user", rate="30/m", block=True)
def list_messages_router(request, conversation_id: UUID):
    user: User = request.auth
    try:
        return 200, list_messages(user_id=user.user_id, conversation_id=conversation_id)
    except ConversationNotFound as e:
        return 404, {"detail": str(e)}
    except PermissionDenied as e:
        return 403, {"detail": str(e)}


@router.post(
    "/conversations/{conversation_id}/messages",
    response={201: MessageOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
    auth=AllRolesAuth(),
    summary="Envia mensagem com anexo(s) (foto, vídeo, PDF ou TXT)",
    description=(
        "multipart/form-data: `content` (texto, opcional se houver anexo) e "
        "`files` (0 a 5 arquivos — imagem/vídeo/PDF/TXT). Mensagem só-texto "
        "sem anexo também funciona aqui, mas pro chat ao vivo prefira o "
        "WebSocket, que tem latência menor."
    ),
)
@ratelimit(key="user", rate="20/m", block=True)
def send_message_router(
    request,
    conversation_id: UUID,
    content: str = Form(""),
    files: List[UploadedFile] = File(None),
):
    user: User = request.auth
    try:
        message = send_message(
            conversation_id=conversation_id,
            sender_id=user.user_id,
            content=content,
            files=files or [],
        )
        return 201, message
    except ConversationNotFound as e:
        return 404, {"detail": str(e)}
    except PermissionDenied as e:
        return 403, {"detail": str(e)}
    except (EmptyMessage, TooManyAttachments) as e:
        return 400, {"detail": str(e)}


@router.post(
    "/conversations/{conversation_id}/read",
    response={200: dict, 403: ErrorOut, 404: ErrorOut},
    auth=AllRolesAuth(),
    summary="Marca as mensagens da conversa como lidas",
)
@ratelimit(key="user", rate="30/m", block=True)
def mark_as_read_router(request, conversation_id: UUID):
    user: User = request.auth
    try:
        updated = mark_conversation_as_read(user_id=user.user_id, conversation_id=conversation_id)
        return 200, {"updated": updated}
    except ConversationNotFound as e:
        return 404, {"detail": str(e)}
    except PermissionDenied as e:
        return 403, {"detail": str(e)}
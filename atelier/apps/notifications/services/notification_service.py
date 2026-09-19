# atelier/apps/notifications/services/notification_service.py
"""
Service layer de Notification.

Convenção do projeto: quando um domínio (payments, reviews, products...)
precisa notificar algo, ele chama um dos helpers `notify_*` passando o ID
do objeto de origem (order_id, reviews_id, product_id...) — nunca a
instância — e é este módulo quem resolve o ID via selector do domínio
correspondente.

Os helpers `notify_*` nunca deixam uma falha de notificação (registro não
encontrado, erro de validação) subir e derrubar a transação de negócio de
quem os chamou — o mesmo princípio já adotado para os e-mails assíncronos
em `payment_service`/`order_service`. Por isso retornam `None` e apenas
logam em caso de erro, em vez de propagar exceção. Diferente dos e-mails,
isso aqui é só um INSERT local (sem chamada de rede), então roda direto,
sem Celery.
"""
import logging
from typing import Optional
from uuid import UUID

from django.db import models

from atelier.apps.accounts.models.user_model import User
from atelier.apps.accounts.selectors.user_selector import get_user_by_id
from atelier.apps.core.exceptions import NotificationNotFound, PermissionDenied, UserNotFound
from atelier.apps.notifications.models.notification import Notification
from atelier.apps.notifications.repositories.notification_repository import (
    create_notification as _create_notification,
    delete_notification as _delete_notification,
    mark_all_as_read as _mark_all_as_read,
    mark_as_read as _mark_as_read,
)
from atelier.apps.notifications.selectors.notification_selector import (
    filter_notifications,
    get_admin_recipients,
    get_notification_by_id,
    get_notifications_for_user,
    get_unread_count,
)

logger = logging.getLogger(__name__)

# ── URLs de ação por rota do front ──────────────────────────────────────────
# Centralizado aqui pra não espalhar strings de rota do front pelos helpers
# `notify_*`. As rotas de cliente já existem e são usadas nos e-mails
# (ver `payment_context.py`); as de admin ficam em branco até o painel
# admin do front definir suas próprias rotas — um link inventado que dá
# 404 é pior que nenhum link.
CLIENT_ORDERS_URL = "/painel/meus-pedidos"
ADMIN_ACTION_URL = ""


def notify(
    *,
    recipient: User,
    notification_type: str,
    title: str,
    body: str = "",
    action_url: str = "",
    actor: Optional[User] = None,
    target: Optional[models.Model] = None,
) -> Notification:
    return _create_notification(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        body=body,
        action_url=action_url,
        actor=actor,
        target=target,
    )


def _safe_notify(notification_type: str, **kwargs) -> Optional[Notification]:
    """
    Envolve `notify()` para que uma falha aqui (registro de origem já
    excluído, corrida rara, etc.) nunca derrube a transação de negócio de
    quem chamou — só loga pra investigação.
    """
    try:
        return notify(notification_type=notification_type, **kwargs)
    except Exception:
        logger.exception("Falha ao criar notificação do tipo %s.", notification_type)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Pedidos (Order / Payment) — cliente
# ═══════════════════════════════════════════════════════════════════════════════

def notify_order_received(order_id: UUID) -> Optional[Notification]:
    from atelier.apps.payments.selectors.order_selector import get_order_by_id

    order = get_order_by_id(order_id=order_id)
    if order is None:
        logger.warning("notify_order_received: pedido %s não encontrado.", order_id)
        return None
    return _safe_notify(
        Notification.NotificationType.ORDER_RECEIVED,
        recipient=order.user_id,
        title="Pedido recebido",
        body=f"Recebemos seu pedido {order.code}. Falta só o pagamento pra confirmar.",
        action_url=CLIENT_ORDERS_URL,
        target=order,
    )


def notify_payment_confirmed(order_id: UUID) -> Optional[Notification]:
    from atelier.apps.payments.selectors.order_selector import get_order_by_id

    order = get_order_by_id(order_id=order_id)
    if order is None:
        logger.warning("notify_payment_confirmed: pedido %s não encontrado.", order_id)
        return None
    return _safe_notify(
        Notification.NotificationType.PAYMENT_CONFIRMED,
        recipient=order.user_id,
        title="Pagamento confirmado",
        body=f"O pagamento do pedido {order.code} foi confirmado. Já vamos preparar suas peças.",
        action_url=CLIENT_ORDERS_URL,
        target=order,
    )


def notify_order_cancelled(order_id: UUID, *, actor: Optional[User] = None) -> Optional[Notification]:
    from atelier.apps.payments.selectors.order_selector import get_order_by_id

    order = get_order_by_id(order_id=order_id)
    if order is None:
        logger.warning("notify_order_cancelled: pedido %s não encontrado.", order_id)
        return None
    return _safe_notify(
        Notification.NotificationType.ORDER_CANCELLED,
        recipient=order.user_id,
        title="Pedido cancelado",
        body=f"O pedido {order.code} foi cancelado.",
        action_url=CLIENT_ORDERS_URL,
        actor=actor,
        target=order,
    )


def notify_payment_refunded(order_id: UUID) -> Optional[Notification]:
    from atelier.apps.payments.selectors.order_selector import get_order_by_id

    order = get_order_by_id(order_id=order_id)
    if order is None:
        logger.warning("notify_payment_refunded: pedido %s não encontrado.", order_id)
        return None
    return _safe_notify(
        Notification.NotificationType.PAYMENT_REFUNDED,
        recipient=order.user_id,
        title="Pagamento estornado",
        body=f"O pagamento do pedido {order.code} foi estornado.",
        action_url=CLIENT_ORDERS_URL,
        target=order,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Avaliações e estoque — admin (backoffice)
# ═══════════════════════════════════════════════════════════════════════════════

def notify_new_review(reviews_id: UUID) -> list[Notification]:
    """Avisa todos os admins que uma avaliação nova chegou e está aguardando autorização."""
    from atelier.apps.reviews.selectors.reviews_selector import get_reviews_by_id

    reviews = get_reviews_by_id(reviews_id=reviews_id)
    if reviews is None:
        logger.warning("notify_new_review: avaliação %s não encontrada.", reviews_id)
        return []

    product_name = reviews.order_item_id.product_id.product_name
    created = []
    for admin in get_admin_recipients():
        notification = _safe_notify(
            Notification.NotificationType.NEW_REVIEW,
            recipient=admin,
            title="Nova avaliação recebida",
            body=f"{product_name} recebeu uma avaliação de {reviews.reviews}★ e aguarda autorização.",
            action_url=ADMIN_ACTION_URL,
            actor=reviews.user_id,
            target=reviews,
        )
        if notification:
            created.append(notification)
    return created


def notify_low_stock(product_id: UUID) -> list[Notification]:
    """
    Avisa todos os admins que um produto está com estoque baixo — mesmo
    sinal usado no dashboard de vendas, só que empurrado na hora em vez de
    esperar alguém abrir o painel. Chame só quando o estoque acabou de
    CRUZAR o limite (ver `order_service.create_order_from_cart`), pra não
    notificar de novo a cada venda enquanto o produto seguir baixo.
    """
    from atelier.apps.products.selectors.product_selector import get_product_by_id

    product = get_product_by_id(product_id=product_id)
    if product is None:
        logger.warning("notify_low_stock: produto %s não encontrado.", product_id)
        return []

    created = []
    for admin in get_admin_recipients():
        notification = _safe_notify(
            Notification.NotificationType.LOW_STOCK,
            recipient=admin,
            title="Estoque baixo",
            body=f"{product.product_name} está com só {product.stock} unidade(s) em estoque.",
            action_url=ADMIN_ACTION_URL,
            target=product,
        )
        if notification:
            created.append(notification)
    return created


# ═══════════════════════════════════════════════════════════════════════════════
# Sistema
# ═══════════════════════════════════════════════════════════════════════════════

def notify_system(*, user_id: UUID, title: str, body: str = "", action_url: str = "") -> Optional[Notification]:
    user = get_user_by_id(user_id=user_id)
    if user is None:
        logger.warning("notify_system: usuário %s não encontrado.", user_id)
        return None
    return _safe_notify(
        Notification.NotificationType.SYSTEM,
        recipient=user,
        title=title,
        body=body,
        action_url=action_url,
        target=None,
    )


# ── Leitura / mutação de estado (com checagem de dono) ──────────────────────
# Estas SIM propagam exceção — são chamadas diretamente pela rota, que
# precisa saber que algo deu errado pra responder o status HTTP certo.

def list_notifications_for_user(*, user_id: UUID, unread_only: bool = False):
    user = get_user_by_id(user_id=user_id)
    if user is None:
        raise UserNotFound()
    return get_notifications_for_user(recipient_id=user.user_id, unread_only=unread_only)


def unread_count_for_user(*, user_id: UUID) -> int:
    user = get_user_by_id(user_id=user_id)
    if user is None:
        raise UserNotFound()
    return get_unread_count(recipient_id=user.user_id)


def mark_notification_as_read(*, user_id: UUID, notification_id: UUID) -> Notification:
    user = get_user_by_id(user_id=user_id)
    if user is None:
        raise UserNotFound()
    notification = get_notification_by_id(notification_id)
    if not notification:
        raise NotificationNotFound()
    if notification.recipient_id != user.user_id:
        raise PermissionDenied("Você não pode alterar notificações de outro usuário.")
    return _mark_as_read(notification)


def mark_all_notifications_as_read(*, user_id: UUID) -> int:
    user = get_user_by_id(user_id=user_id)
    if user is None:
        raise UserNotFound()
    return _mark_all_as_read(user.user_id)


def delete_notification(*, user_id: UUID, notification_id: UUID) -> None:
    user = get_user_by_id(user_id=user_id)
    if user is None:
        raise UserNotFound()
    notification = get_notification_by_id(notification_id)
    if not notification:
        raise NotificationNotFound()
    if notification.recipient_id != user.user_id:
        raise PermissionDenied("Você não pode excluir notificações de outro usuário.")
    _delete_notification(notification)


def list_all_notifications_for_admin(
    *, admin_user_id: UUID, target_user_id: Optional[UUID] = None, read: Optional[bool] = None
):
    admin = get_user_by_id(user_id=admin_user_id)
    if admin is None:
        raise UserNotFound()
    return filter_notifications(user_id=target_user_id, read=read)
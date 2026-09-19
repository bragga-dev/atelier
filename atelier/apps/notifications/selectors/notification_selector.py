from typing import Optional
from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q, QuerySet

from atelier.apps.accounts.models.user_model import User
from atelier.apps.notifications.models.notification import Notification

DEFAULT_RELATED = ("actor", "content_type")


def get_notification_by_id(notification_id: UUID) -> Optional[Notification]:
    return Notification.objects.select_related(*DEFAULT_RELATED).filter(notification_id=notification_id).first()


def get_notifications_for_user(recipient_id: UUID, unread_only: bool = False) -> QuerySet[Notification]:
    qs = Notification.objects.select_related(*DEFAULT_RELATED).filter(recipient_id=recipient_id)
    if unread_only:
        qs = qs.filter(is_read=False)
    return qs.order_by("-created_at")


def get_unread_count(recipient_id: UUID) -> int:
    return Notification.objects.filter(recipient_id=recipient_id, is_read=False).count()


def filter_notifications(user_id: Optional[UUID] = None, read: Optional[bool] = None) -> QuerySet[Notification]:
    """Visão admin: todas as notificações, com filtros opcionais por destinatário e status de leitura."""
    qs = Notification.objects.select_related(*DEFAULT_RELATED).all()
    if user_id is not None:
        qs = qs.filter(recipient_id=user_id)
    if read is not None:
        qs = qs.filter(is_read=read)
    return qs.order_by("-created_at")


def get_admin_recipients() -> QuerySet[User]:
    """Todos os usuários com poder de admin (role ADMIN ou superuser), ativos — usado para notificações in-app dirigidas ao backoffice (ex: nova avaliação pendente, estoque baixo)."""
    return User.objects.filter(Q(role=User.UserRole.ADMIN) | Q(is_superuser=True), is_active=True)


def get_content_type_for_target(target: models.Model) -> ContentType:
    """ContentType do model de origem da notificação (Order, Reviews, Product...)."""
    return ContentType.objects.get_for_model(target)
"""
Repository de Notification — só persistência. Resolver `target` pra
instância (Order, Reviews, Product...) e o seu `ContentType` é
responsabilidade do service.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import QuerySet

from atelier.apps.accounts.models.user_model import User
from atelier.apps.notifications.models.notification import Notification


@transaction.atomic
def create_notification(
    *,
    recipient: User,
    notification_type: str,
    title: str,
    body: str = "",
    action_url: str = "",
    actor: Optional[User] = None,
    content_type: Optional[ContentType] = None,
    object_id: Optional[UUID] = None,
) -> Notification:
    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        title=title,
        body=body,
        action_url=action_url,
        content_type=content_type,
        object_id=object_id,
    )


@transaction.atomic
def mark_as_read(notification: Notification, read_at: datetime) -> Notification:
    notification.is_read = True
    notification.read_at = read_at
    notification.save(update_fields=["is_read", "read_at"])
    return notification


@transaction.atomic
def mark_all_as_read(notifications: QuerySet[Notification], read_at: datetime) -> int:
    """Retorna quantas notificações foram marcadas como lidas."""
    return notifications.update(is_read=True, read_at=read_at)


@transaction.atomic
def delete_notification(notification: Notification) -> None:
    notification.delete()
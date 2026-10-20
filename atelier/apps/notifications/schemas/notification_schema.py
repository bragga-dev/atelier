from django.shortcuts import render

from datetime import datetime
from uuid import UUID

from ninja import Schema


class NotificationOut(Schema):
    notification_id: UUID
    notification_type: str
    title: str
    body: str
    action_url: str
    is_read: bool
    created_at: datetime

    @staticmethod
    def from_orm(obj):
        return NotificationOut(
            notification_id=obj.notification_id,
            notification_type=obj.notification_type,
            title=obj.title,
            body=obj.body,
            action_url=obj.action_url,
            is_read=obj.is_read,
            created_at=obj.created_at,
        )


class UnreadCountOut(Schema):
    unread_count: int


class MarkAllReadOut(Schema):
    updated: int
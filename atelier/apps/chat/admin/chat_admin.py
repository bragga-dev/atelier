from django.contrib import admin

from atelier.apps.chat.models.conversation_model import Conversation
from atelier.apps.chat.models.message_model import Message
from atelier.apps.chat.models.message_attachment_model import MessageAttachment


class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0
    readonly_fields = ("attachment_id", "file_type", "original_filename", "file_size", "created_at")
    can_delete = False


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ("sender", "content", "is_read", "created_at")
    readonly_fields = ("sender", "content", "is_read", "created_at")
    can_delete = False
    show_change_link = True


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("conversation_id", "client", "assigned_admin", "status", "last_message_at")
    list_filter = ("status",)
    search_fields = ("client__email", "subject")
    raw_id_fields = ("client", "assigned_admin", "order")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("message_id", "conversation", "sender", "is_read", "created_at")
    list_filter = ("is_read",)
    raw_id_fields = ("conversation", "sender")
    inlines = [MessageAttachmentInline]
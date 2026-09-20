# atelier/apps/chat/models/message_model.py
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Message(models.Model):
    """
    Uma mensagem dentro de uma Conversation. Pode ter só texto, só
    anexo(s), ou os dois — mas não pode ser totalmente vazia (ver `clean`).
    """

    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey("chat.Conversation", on_delete=models.CASCADE, related_name="messages", verbose_name=_("Conversa"))
    sender = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="sent_messages", verbose_name=_("Remetente"))
    content = models.TextField(_("Mensagem"), blank=True)
    is_read = models.BooleanField(_("Lida"), default=False)
    read_at = models.DateTimeField(_("Lida em"), null=True, blank=True)
    created_at = models.DateTimeField(_("Enviada em"), auto_now_add=True)

    class Meta:
        verbose_name = _("Mensagem")
        verbose_name_plural = _("Mensagens")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["conversation", "is_read"]),
        ]

    def __str__(self):
        preview = self.content[:30] if self.content else "[anexo]"
        return f"{self.sender}: {preview}"

    def clean(self):
        # Só valida texto vazio aqui — "tem pelo menos 1 anexo" depende de
        # `self.attachments`, que só existe depois que a mensagem já tem
        # pk salvo. Essa outra metade da regra fica no service, na hora de
        # criar a mensagem junto com seus anexos.
        super().clean()

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])
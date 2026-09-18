from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
from django.core.validators import MinValueValidator
from atelier.apps.core.validators.image_validator import validate_image_file


class Product(models.Model):

    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_name = models.CharField(_("Nome"), max_length=100, blank=False, null=False)
    categories = models.ManyToManyField(
        "products.ProductCategory",
        related_name="products",
        verbose_name=_("Categorias"),
        help_text=_("Uma peça artesanal pode pertencer a mais de uma categoria (ex.: pulseira de cristais → Pulseiras e Cristais)."),
    )
    price = models.DecimalField(_("Preço"), max_digits=10, decimal_places=2, validators=[MinValueValidator(0, message=_("O preço não pode ser negativo"))])
    stock = models.PositiveIntegerField(_("Estoque"), validators=[MinValueValidator(0, message=_("O estoque não pode ser negativo"))], default=0)
    description = models.TextField(_("Descrição"), blank=True, default="")

    is_active = models.BooleanField(_("Ativa?"), default=True)
    created_at = models.DateTimeField(_("Criada em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Atualizada em"), auto_now=True)

    class Meta:
        verbose_name = _("Produto")
        verbose_name_plural = _("Produtos")
        ordering = ["product_name"]

    def __str__(self):
        return f"{self.product_name}"

    @property
    def in_stock(self) -> bool:
        return self.is_active and self.stock > 0
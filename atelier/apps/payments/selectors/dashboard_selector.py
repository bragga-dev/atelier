"""
Dashboard Selectors — agregações de vendas para o painel do admin.

Nenhuma escrita acontece aqui, só leitura/agregação. As datas recebidas
(`start_date`/`end_date`) filtram por `Order.created_at` (data da compra),
não pela data de entrega/conclusão.
"""
import datetime
from decimal import Decimal
from typing import Iterable, Optional

from django.db.models import DecimalField, F, Sum
from django.db.models.query import QuerySet

from atelier.apps.payments.models.order_item_model import OrderItem
from atelier.apps.payments.models.order_model import Order
from atelier.apps.products.models.product_model import Product

_REVENUE_FIELD = DecimalField(max_digits=12, decimal_places=2)


def _base_order_items_qs(
    start_date: Optional[datetime.date],
    end_date: Optional[datetime.date],
    statuses: Iterable[str],
) -> QuerySet[OrderItem]:
    qs = OrderItem.objects.filter(order_id__order_status__in=list(statuses))
    if start_date:
        qs = qs.filter(order_id__created_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(order_id__created_at__date__lte=end_date)
    return qs


def get_order_totals(
    start_date: Optional[datetime.date],
    end_date: Optional[datetime.date],
    statuses: Iterable[str],
) -> dict:
    qs = Order.objects.filter(order_status__in=list(statuses))
    if start_date:
        qs = qs.filter(created_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__date__lte=end_date)

    total_orders = qs.count()
    total_revenue = qs.aggregate(total=Sum("total_geral"))["total"] or Decimal("0")
    return {"total_orders": total_orders, "total_revenue": total_revenue}


def get_top_products(
    start_date: Optional[datetime.date],
    end_date: Optional[datetime.date],
    statuses: Iterable[str],
    limit: int = 5,
) -> QuerySet:
    qs = _base_order_items_qs(start_date, end_date, statuses)
    return (
        qs.values("product_id", "product_id__product_name")
        .annotate(
            quantity_sold=Sum("order_item_quantity"),
            revenue=Sum(F("order_item_quantity") * F("order_item_price"), output_field=_REVENUE_FIELD),
        )
        .order_by("-quantity_sold")[:limit]
    )


def get_top_categories(
    start_date: Optional[datetime.date],
    end_date: Optional[datetime.date],
    statuses: Iterable[str],
    limit: int = 5,
) -> QuerySet:
    """
    Um item de pedido conta pra cada categoria do produto (se a peça está
    em "Pulseiras" e "Cristais", a venda soma nas duas) — é isso que
    permite ver qual categoria de artesanato reabastecer.
    """
    qs = _base_order_items_qs(start_date, end_date, statuses)
    return (
        qs.filter(product_id__categories__isnull=False)
        .values("product_id__categories", "product_id__categories__category_name")
        .annotate(
            quantity_sold=Sum("order_item_quantity"),
            revenue=Sum(F("order_item_quantity") * F("order_item_price"), output_field=_REVENUE_FIELD),
        )
        .order_by("-quantity_sold")[:limit]
    )


def get_low_stock_products(threshold: int, limit: int = 10) -> QuerySet[Product]:
    return (
        Product.objects.filter(is_active=True, stock__lte=threshold)
        .order_by("stock", "product_name")[:limit]
    )
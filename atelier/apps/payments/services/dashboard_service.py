"""
Dashboard Service — monta o resumo de vendas do admin a partir dos
selectors de agregação.
"""
import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional

from atelier.apps.payments.models.order_model import Order
from atelier.apps.payments.schemas.dashboard_schema import (
    DashboardSummaryOut,
    LowStockProductOut,
    TopCategoryOut,
    TopProductOut,
)
from atelier.apps.payments.selectors.dashboard_selector import (
    get_low_stock_products,
    get_order_totals,
    get_top_categories,
    get_top_products,
)

DEFAULT_STATUSES = [Order.StatusOrder.COMPLETED]
_CENTS = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return (value or Decimal("0")).quantize(_CENTS, rounding=ROUND_HALF_UP)


def get_dashboard_summary(
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    statuses: Optional[List[str]] = None,
    top_n: int = 5,
    low_stock_threshold: int = 5,
) -> DashboardSummaryOut:
    statuses = statuses or DEFAULT_STATUSES

    totals = get_order_totals(start_date, end_date, statuses)
    total_orders = totals["total_orders"]
    total_revenue = _money(totals["total_revenue"])
    average_ticket = _money(total_revenue / total_orders) if total_orders else Decimal("0.00")

    top_products = [
        TopProductOut(
            product_id=row["product_id"],
            product_name=row["product_id__product_name"],
            quantity_sold=row["quantity_sold"],
            revenue=_money(row["revenue"]),
        )
        for row in get_top_products(start_date, end_date, statuses, limit=top_n)
    ]

    top_categories = [
        TopCategoryOut(
            product_category_id=row["product_id__categories"],
            category_name=row["product_id__categories__category_name"],
            quantity_sold=row["quantity_sold"],
            revenue=_money(row["revenue"]),
        )
        for row in get_top_categories(start_date, end_date, statuses, limit=top_n)
    ]

    low_stock_products = [
        LowStockProductOut(product_id=p.product_id, product_name=p.product_name, stock=p.stock)
        for p in get_low_stock_products(threshold=low_stock_threshold)
    ]

    return DashboardSummaryOut(
        period_start=start_date,
        period_end=end_date,
        statuses=list(statuses),
        total_orders=total_orders,
        total_revenue=total_revenue,
        average_ticket=average_ticket,
        top_products=top_products,
        top_categories=top_categories,
        low_stock_products=low_stock_products,
    )
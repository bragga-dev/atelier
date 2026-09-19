"""
Dashboard Schemas — resumo de vendas pro admin: total do período, produtos
e categorias mais vendidos, e produtos com estoque baixo (sinal de que
precisa reabastecer).
"""
import datetime
import uuid
from decimal import Decimal
from typing import List, Optional

from ninja import Schema


class TopProductOut(Schema):
    product_id: uuid.UUID
    product_name: str
    quantity_sold: int
    revenue: Decimal


class TopCategoryOut(Schema):
    product_category_id: uuid.UUID
    category_name: str
    quantity_sold: int
    revenue: Decimal


class LowStockProductOut(Schema):
    product_id: uuid.UUID
    product_name: str
    stock: int


class DashboardSummaryOut(Schema):
    period_start: Optional[datetime.date] = None
    period_end: Optional[datetime.date] = None
    statuses: List[str]
    total_orders: int
    total_revenue: Decimal
    average_ticket: Decimal
    top_products: List[TopProductOut]
    top_categories: List[TopCategoryOut]
    low_stock_products: List[LowStockProductOut]
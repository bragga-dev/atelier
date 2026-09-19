"""
Dashboard admin — resumo de vendas (produtos/categorias mais vendidos,
estoque baixo) e exportação de pedidos em CSV/Excel.
"""
import datetime
from typing import Optional

from django.http import HttpResponse
from django_ratelimit.decorators import ratelimit
from ninja import Router

from atelier.apps.core.permissions.auth_classes import AdminOnlyAuth
from atelier.apps.core.schemas.deafult_schema import MessageOut
from atelier.apps.payments.models.order_model import Order
from atelier.apps.payments.schemas.dashboard_schema import DashboardSummaryOut
from atelier.apps.payments.selectors.order_selector import get_orders_for_export
from atelier.apps.payments.services.dashboard_service import get_dashboard_summary
from atelier.apps.payments.services.order_export_service import render_orders_csv, render_orders_xlsx

router = Router()

VALID_STATUSES = set(Order.StatusOrder.values)


@router.get(
    "/summary",
    response={200: DashboardSummaryOut, 400: MessageOut},
    auth=AdminOnlyAuth(),
    summary="Resumo de vendas: produtos/categorias mais vendidos e estoque baixo",
    description=(
        "Por padrão considera só pedidos `COMPLETED` (vendas confirmadas). "
        "`start_date`/`end_date` filtram pela data da compra (`created_at`). "
        "`top_n` controla quantos produtos/categorias aparecem no ranking. "
        "`low_stock_threshold` define o que conta como estoque baixo "
        "(produtos ativos com `stock` menor ou igual a esse valor)."
    ),
)
@ratelimit(key="user", rate="30/m", block=True)
def dashboard_summary_router(
    request,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    status: Optional[str] = None,
    top_n: int = 5,
    low_stock_threshold: int = 5,
):
    if status and status not in VALID_STATUSES:
        return 400, {"detail": f"Status inválido. Use um de: {', '.join(sorted(VALID_STATUSES))}."}

    statuses = [status] if status else None
    summary = get_dashboard_summary(
        start_date=start_date,
        end_date=end_date,
        statuses=statuses,
        top_n=top_n,
        low_stock_threshold=low_stock_threshold,
    )
    return 200, summary


@router.get(
    "/orders/export",
    response={400: MessageOut},
    auth=AdminOnlyAuth(),
    summary="Exporta pedidos em CSV ou Excel",
    description=(
        "Gera um arquivo pra baixar com um pedido por linha (cliente, "
        "itens resumidos, valores e endereço de entrega) — útil pra "
        "separar/embalar os pedidos manualmente. `format` aceita `csv` "
        "(padrão) ou `xlsx`."
    ),
)
@ratelimit(key="user", rate="10/m", block=True)
def export_orders_router(
    request,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    status: Optional[str] = None,
    format: str = "csv",
):
    if status and status not in VALID_STATUSES:
        return 400, {"detail": f"Status inválido. Use um de: {', '.join(sorted(VALID_STATUSES))}."}

    if format not in ("csv", "xlsx"):
        return 400, {"detail": "Formato inválido. Use 'csv' ou 'xlsx'."}

    statuses = [status] if status else None
    orders = get_orders_for_export(start_date=start_date, end_date=end_date, statuses=statuses)

    filename_bits = ["pedidos"]
    if start_date:
        filename_bits.append(start_date.isoformat())
    if end_date:
        filename_bits.append(end_date.isoformat())
    filename = "_".join(filename_bits)

    if format == "xlsx":
        content = render_orders_xlsx(orders)
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename += ".xlsx"
    else:
        content = render_orders_csv(orders)
        content_type = "text/csv; charset=utf-8"
        filename += ".csv"

    response = HttpResponse(content, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
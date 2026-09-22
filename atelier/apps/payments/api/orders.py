"""
Order endpoints — checkout do carrinho e consulta de pedidos do cliente
autenticado.
"""
import uuid

from ninja import Router, Status
from django_ratelimit.decorators import ratelimit

from atelier.apps.accounts.models.user_model import User
from atelier.apps.payments.models.order_model import Order
from atelier.apps.core.exceptions import EmptyCart, OrderNotFound, OrderNotPayable, UserNotFound
from atelier.apps.core.exceptions.cart_exception import InsufficientStock
from atelier.apps.core.exceptions.permissions import PermissionDenied
from atelier.apps.core.permissions.auth_classes import AdminOnlyAuth, ClientOnlyAuth, ClientCompleteProfileAuth
from atelier.apps.core.schemas.deafult_schema import MessageOut
from atelier.apps.payments.schemas.order_schema import OrderCancelIn, OrderCreateIn, OrderOut
from atelier.apps.payments.services.order_service import (
    cancel_order_by_client,
    create_order_from_cart,
    get_order_for_client,
    list_orders_for_client,
)

from django.shortcuts import get_object_or_404
from atelier.apps.products.integrations.frenet_service import (
    FrenetAPIError,
    FrenetInsufficientBalanceError,
    FrenetService,
)

router = Router()


@router.post(
    "",
    response={201: OrderOut, 400: MessageOut, 403: MessageOut, 404: MessageOut, 409: MessageOut},
    auth=ClientCompleteProfileAuth(),
    summary="Faz o checkout do carrinho e cria um pedido",
)
@ratelimit(key="user", rate="10/m", block=True)
def create_order_router(request, payload: OrderCreateIn):
    try:
        user: User = request.auth
        return Status(201, create_order_from_cart(user.user_id, payload))
    except (UserNotFound, OrderNotFound) as e:
        return Status(404, {"detail": str(e)})
    except PermissionDenied as e:
        return Status(403, {"detail": str(e)})
    except EmptyCart as e:
        return Status(400, {"detail": str(e)})
    except InsufficientStock as e:
        return Status(409, {"detail": str(e)})


@router.get(
    "",
    response={200: list[OrderOut]},
    auth=ClientOnlyAuth(),
    summary="Lista os pedidos do cliente autenticado",
)
@ratelimit(key="user", rate="60/m", block=True)
def list_orders_router(request):
    user: User = request.auth
    return Status(200, list_orders_for_client(user.user_id))


@router.get(
    "/{order_id}",
    response={200: OrderOut, 404: MessageOut},
    auth=ClientOnlyAuth(),
    summary="Retorna um pedido do cliente autenticado",
)
@ratelimit(key="user", rate="60/m", block=True)
def get_order_router(request, order_id: uuid.UUID):
    try:
        user: User = request.auth
        return Status(200, get_order_for_client(user.user_id, order_id))
    except OrderNotFound as e:
        return Status(404, {"detail": str(e)})


@router.post(
    "/{order_id}/cancel",
    response={200: OrderOut, 404: MessageOut, 409: MessageOut},
    auth=ClientOnlyAuth(),
    summary="Cancela um pedido pendente e devolve o estoque",
)
@ratelimit(key="user", rate="10/m", block=True)
def cancel_order_router(request, order_id: uuid.UUID, payload: OrderCancelIn = None):
    try:
        user: User = request.auth
        reason = payload.reason if payload else None
        return Status(200, cancel_order_by_client(user.user_id, order_id, reason=reason))
    except OrderNotFound as e:
        return Status(404, {"detail": str(e)})
    except OrderNotPayable as e:
        return Status(409, {"detail": str(e)})


@router.post(
    "/{order_id}/generate-label",
    response={200: dict, 400: MessageOut, 404: MessageOut, 502: MessageOut},
    auth=AdminOnlyAuth(),
    summary="Gera a etiqueta de envio de um pedido na Frenet (uso administrativo/fulfillment)",
)
def generate_label(request, order_id: uuid.UUID):
    order = get_object_or_404(Order, order_id=order_id)

    if order.shipping_status != Order.ShippingStatus.PENDING:
        return Status(400, {"detail": "Etiqueta já foi gerada para este pedido."})

    if not order.shipping_service_code:
        return Status(400, {"detail": "Pedido não possui um serviço de frete selecionado."})

    service = FrenetService()
    try:
        result = service.create_shipment(order)
    except FrenetInsufficientBalanceError as e:
        return Status(400, {"detail": str(e)})
    except FrenetAPIError as e:
        return Status(502, {"detail": str(e)})

    order.frenet_order_id = result["OrderID"]
    order.shipping_tracking_code = result.get("TrackingNumber")
    order.shipping_label_url = result.get("LabelURL")
    order.shipping_status = Order.ShippingStatus.LABEL_GENERATED
    order.save()

    return Status(200, {"success": True, "tracking_code": order.shipping_tracking_code})
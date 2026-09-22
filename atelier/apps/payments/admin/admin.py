from django.contrib import admin

from atelier.apps.payments.models.asaas_customer_model import AsaasCustomer
from atelier.apps.payments.models.order_item_model import OrderItem
from atelier.apps.payments.models.order_model import Order
from atelier.apps.payments.models.payment_model import Payment
from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html
from django.contrib import messages
from atelier.apps.products.integrations.frenet_service import FrenetService, FrenetInsufficientBalanceError, FrenetAPIError


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_id", "order_item_quantity", "order_item_price")
    can_delete = False


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("billing_type", "status", "value", "asaas_payment_id", "created_at")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("code", "user_id", "order_status", "total_geral", "created_at")
    list_filter = ("order_status", "created_at")
    search_fields = ("code", "user_id__email")
    readonly_fields = ("order_id", "code", "created_at", "updated_at")
    inlines = [OrderItemInline, PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_id", "order_id", "billing_type", "status", "value", "due_date")
    list_filter = ("billing_type", "status")
    search_fields = ("asaas_payment_id", "order_id__code")
    readonly_fields = ("payment_id", "created_at", "updated_at")


@admin.register(AsaasCustomer)
class AsaasCustomerAdmin(admin.ModelAdmin):
    list_display = ("client_id", "asaas_customer_id", "created_at")
    search_fields = ("asaas_customer_id", "client_id__first_name", "client_id__last_name")
    readonly_fields = ("customer_id", "created_at", "updated_at")



# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ["id", "customer", "status", "shipping_status", "generate_label_button"]
#     readonly_fields = ["shipping_tracking_code", "shipping_label_url"]

#     def generate_label_button(self, obj):
#         if obj.shipping_status == Order.ShippingStatus.PENDING:
#             url = reverse("admin:generate-label", args=[obj.pk])
#             return format_html('<a class="button" href="{}">Gerar etiqueta</a>', url)
#         return "✓ Etiqueta gerada"
#     generate_label_button.short_description = "Ação"

#     def get_urls(self):
#         urls = super().get_urls()
#         custom = [
#             path(
#                 "<int:order_id>/generate-label/",
#                 self.admin_site.admin_view(self.generate_label_view),
#                 name="generate-label",
#             ),
#         ]
#         return custom + urls

#     def generate_label_view(self, request, order_id):
#         order = self.get_object(request, order_id)
#         service = FrenetService()

#         try:
#             result = service.create_shipment(order)
#         except FrenetInsufficientBalanceError:
#             messages.error(request, "Saldo insuficiente na Frenet. Adicione crédito na carteira antes de gerar a etiqueta.")
#             return redirect(f"/admin/orders/order/{order_id}/change/")
#         except FrenetAPIError as e:
#             messages.error(request, str(e))
#             return redirect(f"/admin/orders/order/{order_id}/change/")

#         order.frenet_order_id = result["OrderID"]
#         order.shipping_tracking_code = result.get("TrackingNumber")
#         order.shipping_label_url = result.get("LabelURL")
#         order.shipping_status = Order.ShippingStatus.LABEL_GENERATED
#         order.save()
#         messages.success(request, f"Etiqueta gerada: {order.shipping_tracking_code}")
#         return redirect(f"/admin/orders/order/{order_id}/change/")
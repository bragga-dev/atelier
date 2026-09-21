import requests
from django.conf import settings
from atelier.apps.payments.models.order_model import Order


class FrenetInsufficientBalanceError(Exception):
    pass


class FrenetAPIError(Exception):
    pass


class FrenetService:
    BASE_URL = "https://api.frenet.com.br"

    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "token": settings.FRENET_API_KEY,
        }

    def create_shipment(self, order: "Order") -> dict:
        payload = self._build_shipment_payload(order)
        try:
            resp = requests.post(
                f"{self.BASE_URL}/shipping/send",
                json=payload,
                headers=self.headers,
                timeout=15,
            )
            resp.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            data = exc.response.json() if exc.response.content else {}
            message = data.get("Msg", "") or data.get("message", "")

            if exc.response.status_code == 402 or "saldo" in message.lower():
                raise FrenetInsufficientBalanceError(
                    "Saldo insuficiente na carteira Frenet para gerar a etiqueta."
                ) from exc

            raise FrenetAPIError(f"Erro na API Frenet: {message or exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise FrenetAPIError(f"Falha de conexão com a Frenet: {exc}") from exc

        return resp.json()
    def get_label(self, shipment_id: str) -> dict:
        resp = requests.get(
            f"{self.BASE_URL}/shipping/ordertracking/{shipment_id}",
            headers=self.headers,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()


    def _build_shipment_payload(self, order):
        return {
            "SellerCEP": settings.STORE_CEP,
            "RecipientCEP": order.shipping_address.zip_code,
            "ShippingServiceCode": order.shipping_service_code,
            "Invoice": {
                "Number": order.id,
                "TotalValue": float(order.total_value),
            },
            "ShippingItemArray": [
                {
                    "Name": item.product.name,
                    "Quantity": item.quantity,
                    "Weight": item.product.weight,
                }
                for item in order.items.all()
            ],
            "Recipient": {
                "Name": order.customer.name,
                "Email": order.customer.email,
                "Address": order.shipping_address.street,
                "Number": order.shipping_address.number,
                "District": order.shipping_address.district,
                "City": order.shipping_address.city,
                "State": order.shipping_address.state,
                "ZipCode": order.shipping_address.zip_code,
            },
        }
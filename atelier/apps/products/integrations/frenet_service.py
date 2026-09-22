import requests
from django.conf import settings
from atelier.apps.payments.models.order_model import Order


class FrenetInsufficientBalanceError(Exception):
    pass


class FrenetAPIError(Exception):
    pass


class FrenetPartnerTokenMissingError(FrenetAPIError):
    pass


class FrenetService:
    BASE_URL = "https://api.frenet.com.br"

    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "token": settings.FRENET_API_KEY,
        }


    def create_shipment(self, order: "Order") -> dict:
        if not order.shipping_service_code:
            raise FrenetAPIError(
                "Pedido não possui um serviço de frete (shipping_service_code) selecionado."
            )

        # A geração de etiqueta (Orders Oneclick) roda na API Whitelabel da
        # Frenet, que exige um Partner Token além do token do cliente. Esse
        # token só é emitido pelo time de Parcerias da Frenet após um
        # processo de homologação — enquanto não configurado, falhamos aqui
        # com uma mensagem clara em vez de bater num endpoint que não existe
        # mais na API antiga (o que gerava 502 com HTML de erro).
        if not getattr(settings, "FRENET_PARTNER_TOKEN", ""):
            raise FrenetPartnerTokenMissingError(
                "Geração de etiqueta indisponível: falta configurar o "
                "FRENET_PARTNER_TOKEN (Partner Token da Frenet, obtido após "
                "homologação com o time de Parcerias). A API de pedidos/"
                "etiquetas da Frenet roda na Whitelabel v1 e exige esse "
                "token além do FRENET_API_KEY."
            )

        # TODO: assim que o Partner Token for liberado, trocar a chamada
        # abaixo pelo endpoint real da Whitelabel (Orders Oneclick), usando
        # settings.FRENET_WHITELABEL_BASE_URL e o header x-partner-token —
        # o payload precisa ser conferido contra a documentação/sandbox
        # deles nesse momento, pois o formato é diferente do usado na
        # cotação (api.frenet.com.br).
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
            try:
                data = exc.response.json() if exc.response.content else {}
            except ValueError:
                data = {}
            message = data.get("Msg", "") or data.get("message", "") or exc.response.text

            if exc.response.status_code == 402 or "saldo" in message.lower():
                raise FrenetInsufficientBalanceError(
                    "Saldo insuficiente na carteira Frenet para gerar a etiqueta."
                ) from exc

            raise FrenetAPIError(f"Erro na API Frenet: {message or exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise FrenetAPIError(f"Falha de conexão com a Frenet: {exc}") from exc

        try:
            return resp.json()
        except ValueError as exc:
            raise FrenetAPIError(
                "A Frenet retornou uma resposta em formato inesperado (não-JSON) para o envio."
            ) from exc

    def get_label(self, shipment_id: str) -> dict:
        resp = requests.get(
            f"{self.BASE_URL}/shipping/ordertracking/{shipment_id}",
            headers=self.headers,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()


    def _build_shipment_payload(self, order):
        client = getattr(order.user_id, "client_profile", None)
        recipient_name = client.get_full_name() if client else order.user_id.email

        return {
            "SellerCEP": settings.STORE_CEP,
            "RecipientCEP": order.shipping_address.cep,
            "ShippingServiceCode": order.shipping_service_code,
            "Invoice": {
                "Number": order.code,
                "TotalValue": float(order.total_geral),
            },
            "ShippingItemArray": [
                {
                    "Name": item.product_id.product_name,
                    "Quantity": item.order_item_quantity,
                    "Weight": float(item.product_id.shipping.weight),
                }
                for item in order.items.all()
            ],
            "Recipient": {
                "Name": recipient_name,
                "Email": order.user_id.email,
                "Address": order.shipping_address.street,
                "Number": order.shipping_address.number,
                "District": order.shipping_address.neighborhood,
                "City": order.shipping_address.city,
                "State": order.shipping_address.state,
                "ZipCode": order.shipping_address.cep,
            },
        }
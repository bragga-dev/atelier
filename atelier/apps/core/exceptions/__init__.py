from atelier.apps.core.exceptions.auth import InvalidCredentials, InvalidPassword, InvalidToken, InvalidGoogleToken, SessionNotFound
from atelier.apps.core.exceptions.user import UserAlreadyExists, UserNotFound, EmailNotVerified
from atelier.apps.core.exceptions.permissions import PermissionDenied
from atelier.apps.core.exceptions.media import InvalidImageFile
from atelier.apps.core.exceptions.contact_exception import ContactNameAlreadyExists, ContactNotFound
from atelier.apps.core.exceptions.shipping import FrenetAPIError
from atelier.apps.core.exceptions.cart_exception import CartNotFound, CartItemNotFound, InsufficientStock
from atelier.apps.core.exceptions.payment_exception import (
    
    AsaasAPIError,
    OrderNotFound,
    EmptyCart,
    OrderNotPayable,
    OrderAlreadyPaid,
    PaymentNotFound,
    CpfOrCnpjRequired,
    PaymentNotRefundable,
    InvalidWebhookToken,
    InvalidOrderStatusTransition,
)

from atelier.apps.core.exceptions.products_exception import (
    ProductNotFound,
    ProductNameAlreadyExists,
    CategoryNotFound,
    CategoryNameAlreadyExists,
    CategoryHasProducts,
    ImageNotFound,
    ShippingNotFound,
    ShippingAlreadyExists,
)
from atelier.apps.core.exceptions.campaign_exception import CampaignNotFound, CampaignTitleAlreadyExists, CampaignImageNotFound
from atelier.apps.core.exceptions.notification_exception import NotificationNotFound
from atelier.apps.core.exceptions.chat_exception import (
    ConversationNotFound,
    MessageNotFound,
    EmptyMessage,
    TooManyAttachments,
)

__all__ = [
    
    "InvalidCredentials",
    "InvalidPassword", 
    "InvalidToken",
    "InvalidGoogleToken",
    "SessionNotFound",
    "UserAlreadyExists",
    "UserNotFound",
    "PermissionDenied",
    "EmailNotVerified",
    "InvalidImageFile",
    "ContactNameAlreadyExists",
    "ContactNotFound",

    "FrenetAPIError",

    "CartNotFound",
    "CartItemNotFound",
    "InsufficientStock",

    "ProductNotFound",
    "ProductNameAlreadyExists",
    "CategoryNotFound",
    "CategoryNameAlreadyExists",
    "CategoryHasProducts",
    "ImageNotFound",
    "ShippingNotFound",
    "ShippingAlreadyExists",

    "AsaasAPIError",
    "OrderNotFound",
    "EmptyCart",
    "OrderNotPayable",
    "OrderAlreadyPaid",
    "PaymentNotFound",
    "CpfOrCnpjRequired",
    "PaymentNotRefundable",
    "InvalidWebhookToken",
    "InvalidOrderStatusTransition",

    "CampaignNotFound",
    "CampaignTitleAlreadyExists",
    "CampaignImageNotFound",

    "NotificationNotFound",

    "ConversationNotFound",
    "MessageNotFound",
    "EmptyMessage",
    "TooManyAttachments",

]
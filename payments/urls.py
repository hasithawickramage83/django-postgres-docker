from django.urls import path
from .views import create_stripe_checkout_session, finalize_order, stripe_webhook, CreateRefundView

urlpatterns = [
    path("create-checkout-session/", create_stripe_checkout_session, name="create-checkout-session"),
    path("finalize-order/", finalize_order, name="finalize-order"),
    path("refund/", CreateRefundView.as_view(), name="refund"),
    path("webhook/", stripe_webhook, name="stripe-webhook"),
]
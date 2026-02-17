from django.urls import path
from .views import AddToCartView, CartView, CheckoutView,MyOrdersView, OrderDetailView,RemoveFromCartView

urlpatterns = [
    path("cart/add/", AddToCartView.as_view(), name="cart-add"),
    path("cart/", CartView.as_view(), name="cart-view"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path('', MyOrdersView.as_view(), name='my-orders'),  # GET /api/orders/
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),  # GET /api/orders/<id>/
    path('cart/remove/<int:item_id>/', RemoveFromCartView.as_view(), name='remove-from-cart'),
]

from django.urls import path
from .views import (
    AddToCartView, ReduceFromCartView, CartView, RemoveFromCartView,
    MyOrdersView, OrderDetailView,
    CreateCheckoutSessionView, FinalizeOrderView
)

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/add/', AddToCartView.as_view(), name='add_to_cart'),
    path('cart/reduce/', ReduceFromCartView.as_view(), name='reduce_from_cart'),
    path('cart/remove/<int:item_id>/', RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('checkout/', CreateCheckoutSessionView.as_view(), name='create_checkout_session'),
    path('finalize-order/', FinalizeOrderView.as_view(), name='finalize_order'),
    path('orders/', MyOrdersView.as_view(), name='my_orders'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
]
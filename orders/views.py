from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from products.models import Product
from .models import Order, OrderItem
from .serializers import OrderSerializer

class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))

        if quantity <= 0:
            return Response({"error": "Quantity must be greater than zero"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id, is_active=True)

        if product.quantity < quantity:
            return Response({"error": "Not enough stock available"}, status=status.HTTP_400_BAD_REQUEST)

        order, _ = Order.objects.get_or_create(user=user, status=Order.Status.PENDING)

        item, created = OrderItem.objects.get_or_create(
            order=order,
            product=product,
            defaults={"quantity": quantity, "price": product.price}
        )
        if not created:
            item.quantity += quantity
            item.save()

        return Response({"message": "Product added to cart"}, status=status.HTTP_200_OK)


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        order = Order.objects.filter(user=request.user, status=Order.Status.PENDING).first()
        if not order:
            return Response({"message": "Cart is empty"}, status=status.HTTP_200_OK)
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        order = Order.objects.filter(user=request.user, status=Order.Status.PENDING).select_for_update().first()
        if not order:
            return Response({"error": "No pending order found"}, status=status.HTTP_400_BAD_REQUEST)

        for item in order.items.all():
            product = item.product
            if product.quantity < item.quantity:
                return Response({"error": f"Not enough stock for {product.name}"}, status=status.HTTP_400_BAD_REQUEST)
            product.quantity -= item.quantity
            product.save()

        order.status = Order.Status.ORDERED
        order.save()

        return Response({"message": "Order placed successfully"}, status=status.HTTP_200_OK)



# --- ORDER LIST / DETAILS ---

class MyOrdersView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Return only the logged-in user's orders, newest first
        return Order.objects.filter(user=self.request.user).order_by('-id')


class OrderDetailView(RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
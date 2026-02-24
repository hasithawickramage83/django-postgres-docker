import stripe
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from backend import settings
from products.models import Product
from .models import Order, OrderItem
from .serializers import OrderSerializer

class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))

        if quantity < 0:
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

class ReduceFromCartView(APIView):
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
            item.quantity -= quantity
            item.save()

        return Response({"message": "Product reduced from cart"}, status=status.HTTP_200_OK)

class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        order = Order.objects.filter(user=request.user, status=Order.Status.PENDING).first()
        if not order:
            return Response({"message": "Cart is empty"}, status=status.HTTP_200_OK)
        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        order = Order.objects.filter(user=request.user, status=Order.Status.PENDING).select_for_update().first()
        if not order or not order.items.exists():
            return Response({"error": "No items in cart"}, status=status.HTTP_400_BAD_REQUEST)

        # Check stock
        for item in order.items.all():
            if item.product.quantity < item.quantity:
                return Response({"error": f"Not enough stock for {item.product.name}"}, status=status.HTTP_400_BAD_REQUEST)

        # Build line items for Stripe
        line_items = []
        for item in order.items.all():
            price = int(item.price * 100)  # Stripe uses cents
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': item.product.name},
                    'unit_amount': price,
                },
                'quantity': item.quantity,
            })

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=f"{settings.FRONTEND_URL}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/cart",
            metadata={'order_id': order.id}
        )

        return Response({"url": session.url})
class FinalizeOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        session_id = request.data.get("session_id")
        if not session_id:
            return Response({"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            order_id = session.metadata.get("order_id")
            order = Order.objects.select_for_update().get(id=order_id, user=request.user)

            if session.payment_status != 'paid':
                return Response({"error": "Payment not completed"}, status=status.HTTP_400_BAD_REQUEST)

            # Reduce stock
            for item in order.items.all():
                product = item.product
                if product.quantity < item.quantity:
                    return Response({"error": f"Not enough stock for {product.name}"}, status=status.HTTP_400_BAD_REQUEST)
                product.quantity -= item.quantity
                product.save()

            order.status = Order.Status.ORDERED
            order.save()

            return Response({"message": "Order finalized successfully", "order_id": order.id})

        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class RemoveFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        """
        Delete a specific OrderItem from the user's pending cart.
        """
        # Get the user's pending order
        order = Order.objects.filter(user=request.user, status=Order.Status.PENDING).first()
        if not order:
            return Response({"error": "No pending cart found"}, status=status.HTTP_400_BAD_REQUEST)

        # Get the item to delete
        item = order.items.filter(id=item_id).first()
        if not item:
            return Response({"error": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND)

        # Delete the item
        item.delete()
        return Response({"message": "Item removed from cart"}, status=status.HTTP_200_OK)


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


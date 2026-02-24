import stripe
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from payments.models import Payment, Refund

stripe.api_key = settings.STRIPE_SECRET_KEY


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_stripe_checkout_session(request):
    """
    Create Stripe Checkout Session for an existing order
    """
    order_id = request.data.get('order_id')
    if not order_id:
        return Response({"error": "Order ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status != Order.Status.PENDING:
        return Response({"error": "Order cannot be paid"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"Order #{order.id}",
                    },
                    'unit_amount': int(order.total_price() * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{settings.FRONTEND_URL}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/cart",
            metadata={'order_id': order.id},
        )
        return Response({"url": session.url})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def finalize_order(request):
    """
    After Stripe Checkout redirects back, confirm payment and update order
    """
    session_id = request.data.get('session_id')
    if not session_id:
        return Response({"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        order_id = session.metadata.get('order_id')
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if session.payment_status != 'paid':
            return Response({"error": "Payment not completed"}, status=status.HTTP_400_BAD_REQUEST)

        # Update order status
        order.status = Order.Status.ORDERED
        order.save()

        # Create Payment record
        Payment.objects.create(
            order=order,
            amount=order.total_price(),
            payment_method=Payment.PaymentMethod.CARD,
            stripe_payment_intent_id=session.payment_intent,
            status=Payment.Status.SUCCEEDED,
        )

        return Response({"message": "Order finalized successfully", "order_id": order.id})

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Keep your existing refund and webhook code
class CreateRefundView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from .serializers import CreateRefundSerializer
        serializer = CreateRefundSerializer(data=request.data)
        if serializer.is_valid():
            payment_id = serializer.validated_data['payment_id']
            amount = serializer.validated_data['amount']
            reason = serializer.validated_data['reason']

            try:
                payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)

                if payment.status != Payment.Status.SUCCEEDED:
                    return Response(
                        {'error': 'Payment cannot be refunded'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if amount > payment.amount:
                    return Response(
                        {'error': 'Refund amount cannot exceed payment amount'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                refund_obj = Refund.objects.create(
                    payment=payment,
                    amount=amount,
                    reason=reason,
                    status=Refund.Status.PENDING
                )

                stripe_refund = stripe.Refund.create(
                    payment_intent=payment.stripe_payment_intent_id,
                    amount=int(amount * 100),
                    reason='requested_by_customer',
                    metadata={'refund_id': refund_obj.id}
                )

                refund_obj.stripe_refund_id = stripe_refund.id
                refund_obj.status = Refund.Status.SUCCEEDED
                refund_obj.save()

                return Response({
                    'refund_id': refund_obj.id,
                    'amount': amount,
                    'status': 'succeeded',
                    'message': 'Refund processed successfully'
                })

            except Payment.DoesNotExist:
                return Response(
                    {'error': 'Payment not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except stripe.error.StripeError as e:
                refund_obj.status = Refund.Status.FAILED
                refund_obj.failure_reason = str(e)
                refund_obj.save()
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    if event.type == 'checkout.session.completed':
        session = event.data.object
        order_id = session.metadata.get('order_id')
        try:
            order = Order.objects.get(id=order_id)
            order.status = Order.Status.ORDERED
            order.save()

            Payment.objects.get_or_create(
                order=order,
                stripe_payment_intent_id=session.payment_intent,
                defaults={
                    'amount': order.total_price(),
                    'payment_method': Payment.PaymentMethod.CARD,
                    'status': Payment.Status.SUCCEEDED
                }
            )
        except Order.DoesNotExist:
            pass

    return JsonResponse({'status': 'success'})
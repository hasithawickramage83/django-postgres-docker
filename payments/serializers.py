from rest_framework import serializers
from .models import Payment, Refund
from orders.serializers import OrderSerializer


class PaymentSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    order_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_id', 'stripe_payment_intent_id', 
            'stripe_session_id', 'amount', 'currency', 'status', 
            'payment_method', 'stripe_customer_id', 'failure_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'stripe_payment_intent_id', 'stripe_session_id', 
            'stripe_customer_id', 'failure_reason', 'created_at', 'updated_at'
        ]


class CreatePaymentIntentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(
        choices=Payment.PaymentMethod.choices,
        default=Payment.PaymentMethod.CARD
    )


class ConfirmPaymentSerializer(serializers.Serializer):
    payment_intent_id = serializers.CharField()
    payment_method_id = serializers.CharField(required=False)


class RefundSerializer(serializers.ModelSerializer):
    payment_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Refund
        fields = [
            'id', 'payment', 'payment_id', 'stripe_refund_id', 
            'amount', 'reason', 'status', 'failure_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'payment', 'stripe_refund_id', 'status', 
            'failure_reason', 'created_at', 'updated_at'
        ]


class CreateRefundSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.CharField(max_length=500)

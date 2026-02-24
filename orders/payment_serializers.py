from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer
from payments.serializers import PaymentSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].context.update({'request': self.context.get('request')})

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'created_at', 'updated_at']


class OrderWithPaymentSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    payment = PaymentSerializer(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['items'].context.update(self.context)

    class Meta:
        model = Order
        fields = ['id', 'status', 'items', 'total_price', 'payment', 'created_at', 'updated_at']

    @staticmethod
    def get_total_price(obj):
        return obj.total_price()

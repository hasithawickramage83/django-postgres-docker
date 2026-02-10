from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer  # assuming you already have ProductSerializer

# Serializer for each order item
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'created_at', 'updated_at']


# Serializer for the order itself
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order  # model stays Order
        fields = ['id', 'status', 'items', 'total_price', 'created_at', 'updated_at']

    def get_total_price(self, obj):
        return obj.total_price()

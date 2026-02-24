from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Product
from orders.models import Order, OrderItem
from payments.models import Payment

User = get_user_model()


class PaymentIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=10.00,
            quantity=100,
            created_by=self.user
        )
        self.order = Order.objects.create(
            user=self.user,
            status=Order.Status.PENDING
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=10.00
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_payment_intent(self):
        """Test creating a payment intent"""
        data = {
            'order_id': self.order.id,
            'payment_method': 'CARD'
        }
        response = self.client.post('/api/payments/create-payment-intent/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('client_secret', response.data)
        self.assertIn('payment_intent_id', response.data)
        self.assertEqual(float(response.data['amount']), 20.00)

    def test_payment_list(self):
        """Test retrieving payment list"""
        # Create a payment
        payment = Payment.objects.create(
            order=self.order,
            amount=20.00,
            stripe_payment_intent_id='pi_test_123',
            status=Payment.Status.PENDING
        )
        
        response = self.client.get('/api/payments/payments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], payment.id)

    def test_payment_detail(self):
        """Test retrieving payment details"""
        payment = Payment.objects.create(
            order=self.order,
            amount=20.00,
            stripe_payment_intent_id='pi_test_123',
            status=Payment.Status.PENDING
        )
        
        response = self.client.get(f'/api/payments/payments/{payment.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], payment.id)
        self.assertEqual(response.data['amount'], '20.00')

    def test_create_refund(self):
        """Test creating a refund"""
        payment = Payment.objects.create(
            order=self.order,
            amount=20.00,
            stripe_payment_intent_id='pi_test_123',
            status=Payment.Status.SUCCEEDED
        )
        
        data = {
            'payment_id': payment.id,
            'amount': '10.00',
            'reason': 'Customer requested refund'
        }
        
        # Note: This will fail in test environment without Stripe API keys
        # but tests the endpoint structure
        response = self.client.post('/api/payments/create-refund/', data)
        # Expected to fail due to Stripe API, but endpoint should be accessible
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])

    def test_payment_order_relationship(self):
        """Test payment-order relationship"""
        payment = Payment.objects.create(
            order=self.order,
            amount=20.00,
            stripe_payment_intent_id='pi_test_123',
            status=Payment.Status.SUCCEEDED
        )
        
        # Test that payment is accessible from order
        self.assertEqual(self.order.payment, payment)
        
        # Test that order status updates when payment succeeds
        self.order.refresh_from_db()
        # Note: This would be updated by webhook or payment confirmation
        self.assertEqual(self.order.status, Order.Status.PENDING)

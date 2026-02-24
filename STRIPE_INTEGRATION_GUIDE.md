# Stripe Integration Guide

This guide explains how to integrate Stripe payments into your Django e-commerce application.

## Overview

The Stripe integration includes:
- **Backend**: Django REST API endpoints for payment processing
- **Frontend**: JavaScript examples for client-side payment handling
- **Webhooks**: Stripe webhook handling for payment status updates

## Backend Setup

### 1. Install Dependencies
```bash
pip install stripe
```

### 2. Environment Variables
Add these to your `.env` file:
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 3. Database Migration
Run migrations to create payment tables:
```bash
python manage.py makemigrations payments
python manage.py migrate
```

### 4. API Endpoints

#### Create Payment Intent
```
POST /api/payments/create-payment-intent/
Authorization: Bearer <token>
Content-Type: application/json

{
    "order_id": 1,
    "payment_method": "CARD"
}
```

Response:
```json
{
    "client_secret": "pi_...",
    "payment_intent_id": "pi_...",
    "amount": "99.99",
    "currency": "usd"
}
```

#### Confirm Payment
```
POST /api/payments/confirm-payment/
Authorization: Bearer <token>
Content-Type: application/json

{
    "payment_intent_id": "pi_1234567890"
}
```

#### Get Payment History
```
GET /api/payments/payments/
Authorization: Bearer <token>
```

#### Request Refund
```
POST /api/payments/create-refund/
Authorization: Bearer <token>
Content-Type: application/json

{
    "payment_id": 1,
    "amount": "50.00",
    "reason": "Customer requested refund"
}
```

#### Stripe Webhook
```
POST /api/payments/webhook/stripe/
```

## Frontend Integration

### 1. Include Stripe.js
```html
<script src="https://js.stripe.com/v3/"></script>
```

### 2. Basic Payment Form
See `frontend_examples/stripe_payment.html` for a complete example.

### 3. Using the Payment Manager
```javascript
// Initialize
const paymentManager = new StripePaymentManager('pk_test_...');
paymentManager.initializeCard('card-element');

// Process payment
document.getElementById('pay-button').addEventListener('click', async () => {
    const orderId = document.getElementById('order-id').value;
    const result = await paymentManager.processPayment(orderId);
    
    if (result.success) {
        alert('Payment successful!');
        window.location.href = '/order-success';
    } else {
        alert('Payment failed: ' + result.error);
    }
});
```

## Payment Flow

1. **Create Payment Intent**: Client requests a payment intent from the backend
2. **Collect Card Details**: Stripe Elements securely collects card information
3. **Confirm Payment**: Client confirms payment with Stripe using the client secret
4. **Backend Confirmation**: Client notifies backend of successful payment
5. **Order Status Update**: Backend updates order status to "ORDERED"
6. **Webhook Handling**: Stripe sends webhook to confirm payment status

## Security Considerations

- Never expose your secret key on the frontend
- Always use HTTPS in production
- Validate webhook signatures
- Implement proper authentication on all payment endpoints
- Use Stripe Elements for secure card data collection

## Testing

### Test Cards
Use these test card numbers for testing:
- **Success**: 4242 4242 4242 4242
- **Requires 3D Secure**: 4000 0025 0000 3155
- **Declined**: 4000 0000 0000 0002

### Test Scenarios
1. Successful payment
2. Failed payment (declined card)
3. 3D Secure authentication
4. Partial refunds
5. Webhook processing

## Production Deployment

1. **Update Keys**: Replace test keys with live keys
2. **Domain Registration**: Add your domain to Stripe account
3. **Webhook URL**: Configure production webhook URL
4. **SSL Certificate**: Ensure HTTPS is properly configured
5. **Error Handling**: Implement robust error handling and logging

## Common Issues

### Payment Intent Creation Fails
- Check if order exists and belongs to the user
- Verify order status is PENDING
- Ensure Stripe secret key is correct

### Card Element Not Loading
- Verify Stripe.js is loaded
- Check publishable key is correct
- Ensure container element exists

### Webhook Not Working
- Verify webhook URL is accessible
- Check webhook secret in settings
- Ensure webhook events are enabled in Stripe dashboard

## Support

For issues related to:
- **Stripe API**: Check Stripe documentation at https://stripe.com/docs
- **Django Integration**: Review this guide and code examples
- **Frontend Issues**: Use browser developer tools for debugging

## API Response Codes

- **200**: Success
- **400**: Bad Request (validation error, Stripe error)
- **401**: Unauthorized (invalid/missing token)
- **403**: Forbidden (user doesn't own the resource)
- **404**: Not Found (order/payment doesn't exist)
- **500**: Server Error

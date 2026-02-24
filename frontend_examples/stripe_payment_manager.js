// Stripe Payment Integration Helper Class
class StripePaymentManager {
    constructor(publishableKey) {
        this.stripe = Stripe(publishableKey);
        this.elements = this.stripe.elements();
        this.card = null;
    }

    // Initialize card element
    initializeCard(elementId) {
        this.card = this.elements.create('card');
        this.card.mount(`#${elementId}`);
        
        this.card.on('change', ({error}) => {
            const displayError = document.getElementById('card-errors');
            if (error) {
                displayError.textContent = error.message;
            } else {
                displayError.textContent = '';
            }
        });
    }

    // Create payment intent
    async createPaymentIntent(orderId, paymentMethod = 'CARD') {
        const response = await fetch('/api/payments/create-payment-intent/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getAuthToken()}`
            },
            body: JSON.stringify({
                order_id: orderId,
                payment_method: paymentMethod
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create payment intent');
        }

        return await response.json();
    }

    // Confirm payment with Stripe
    async confirmPayment(clientSecret, paymentMethodData = {}) {
        const {error, paymentIntent} = await this.stripe.confirmCardPayment(clientSecret, {
            payment_method: {
                card: this.card,
                ...paymentMethodData
            }
        });

        if (error) {
            throw new Error(error.message);
        }

        return paymentIntent;
    }

    // Confirm payment on backend
    async confirmPaymentOnBackend(paymentIntentId) {
        const response = await fetch('/api/payments/confirm-payment/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getAuthToken()}`
            },
            body: JSON.stringify({
                payment_intent_id: paymentIntentId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to confirm payment');
        }

        return await response.json();
    }

    // Process complete payment flow
    async processPayment(orderId, paymentMethodData = {}) {
        try {
            // Step 1: Create payment intent
            const paymentData = await this.createPaymentIntent(orderId);
            
            // Step 2: Confirm payment with Stripe
            const paymentIntent = await this.confirmPayment(paymentData.client_secret, paymentMethodData);
            
            // Step 3: Confirm on backend
            const result = await this.confirmPaymentOnBackend(paymentIntent.id);
            
            return {
                success: true,
                paymentIntent,
                backendResult: result
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    // Get authentication token from localStorage
    getAuthToken() {
        return localStorage.getItem('access_token');
    }

    // Get payment history
    async getPaymentHistory() {
        const response = await fetch('/api/payments/payments/', {
            headers: {
                'Authorization': `Bearer ${this.getAuthToken()}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch payment history');
        }

        return await response.json();
    }

    // Get payment details
    async getPaymentDetails(paymentId) {
        const response = await fetch(`/api/payments/payments/${paymentId}/`, {
            headers: {
                'Authorization': `Bearer ${this.getAuthToken()}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch payment details');
        }

        return await response.json();
    }

    // Request refund
    async requestRefund(paymentId, amount, reason) {
        const response = await fetch('/api/payments/create-refund/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getAuthToken()}`
            },
            body: JSON.stringify({
                payment_id: paymentId,
                amount: amount,
                reason: reason
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to process refund');
        }

        return await response.json();
    }
}

// Usage Example:
// const paymentManager = new StripePaymentManager('pk_test_...');
// paymentManager.initializeCard('card-element');
// 
// document.getElementById('pay-button').addEventListener('click', async () => {
//     const orderId = document.getElementById('order-id').value;
//     const result = await paymentManager.processPayment(orderId);
//     
//     if (result.success) {
//         alert('Payment successful!');
//     } else {
//         alert('Payment failed: ' + result.error);
//     }
// });

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StripePaymentManager;
}

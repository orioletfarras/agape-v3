"""Stripe Service for payment processing"""
import logging
from typing import Optional, Dict, Any
from decimal import Decimal
import stripe

from app.infrastructure.config import settings

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for processing payments via Stripe"""

    def __init__(self):
        self.publishable_key = settings.STRIPE_PUBLISHABLE_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.currency = settings.STRIPE_CURRENCY.lower()

    def _amount_to_cents(self, amount: Decimal) -> int:
        """Convert amount to cents (Stripe uses smallest currency unit)"""
        return int(amount * 100)

    def _cents_to_amount(self, cents: int) -> Decimal:
        """Convert cents to amount"""
        return Decimal(cents) / 100

    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Create a Stripe customer

        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata

        Returns:
            str: Stripe customer ID or None if failed
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {},
            )
            logger.info(f"Stripe customer created: {customer.id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {e}")
            return None

    async def create_payment_intent(
        self,
        amount: Decimal,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a payment intent

        Args:
            amount: Payment amount
            customer_id: Stripe customer ID (optional)
            metadata: Additional metadata
            description: Payment description

        Returns:
            dict: Payment intent data or None if failed
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=self._amount_to_cents(amount),
                currency=self.currency,
                customer=customer_id,
                metadata=metadata or {},
                description=description,
                automatic_payment_methods={"enabled": True},
            )

            logger.info(f"Payment intent created: {intent.id} for amount {amount}")

            return {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
                "amount": self._cents_to_amount(intent.amount),
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating payment intent: {e}")
            return None

    async def create_checkout_session(
        self,
        price: Decimal,
        product_name: str,
        quantity: int = 1,
        success_url: str = None,
        cancel_url: str = None,
        customer_email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        mode: str = "payment",
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Stripe Checkout session

        Args:
            price: Product price
            product_name: Product name
            quantity: Quantity
            success_url: Success redirect URL
            cancel_url: Cancel redirect URL
            customer_email: Customer email
            metadata: Additional metadata
            mode: "payment" or "subscription"

        Returns:
            dict: Checkout session data or None if failed
        """
        try:
            success_url = success_url or f"{settings.FRONTEND_URL}/payment/success"
            cancel_url = cancel_url or f"{settings.FRONTEND_URL}/payment/cancel"

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": self.currency,
                            "unit_amount": self._amount_to_cents(price),
                            "product_data": {
                                "name": product_name,
                            },
                        },
                        "quantity": quantity,
                    }
                ],
                mode=mode,
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url,
                customer_email=customer_email,
                metadata=metadata or {},
            )

            logger.info(f"Checkout session created: {session.id}")

            return {
                "session_id": session.id,
                "checkout_url": session.url,
                "status": session.status,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating checkout session: {e}")
            return None

    async def create_subscription(
        self,
        customer_id: str,
        price_amount: Decimal,
        product_name: str,
        interval: str = "month",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a subscription

        Args:
            customer_id: Stripe customer ID
            price_amount: Monthly/yearly price
            product_name: Product name
            interval: "month" or "year"
            metadata: Additional metadata

        Returns:
            dict: Subscription data or None if failed
        """
        try:
            # Create a product
            product = stripe.Product.create(name=product_name)

            # Create a price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=self._amount_to_cents(price_amount),
                currency=self.currency,
                recurring={"interval": interval},
            )

            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price.id}],
                metadata=metadata or {},
            )

            logger.info(f"Subscription created: {subscription.id}")

            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating subscription: {e}")
            return None

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription"""
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            logger.info(f"Subscription cancelled: {subscription_id}")
            return subscription.status == "canceled"

        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling subscription: {e}")
            return False

    async def retrieve_payment_intent(self, payment_intent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve payment intent details"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "payment_intent_id": intent.id,
                "status": intent.status,
                "amount": self._cents_to_amount(intent.amount),
                "currency": intent.currency,
                "customer": intent.customer,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving payment intent: {e}")
            return None

    async def retrieve_checkout_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve checkout session details"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)

            return {
                "session_id": session.id,
                "payment_status": session.payment_status,
                "status": session.status,
                "amount_total": self._cents_to_amount(session.amount_total) if session.amount_total else None,
                "customer": session.customer,
                "payment_intent": session.payment_intent,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving checkout session: {e}")
            return None

    async def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Refund a payment

        Args:
            payment_intent_id: Payment intent ID
            amount: Refund amount (None for full refund)
            reason: Refund reason

        Returns:
            dict: Refund data or None if failed
        """
        try:
            refund_params = {"payment_intent": payment_intent_id}

            if amount:
                refund_params["amount"] = self._amount_to_cents(amount)

            if reason:
                refund_params["reason"] = reason

            refund = stripe.Refund.create(**refund_params)

            logger.info(f"Refund created: {refund.id} for payment intent {payment_intent_id}")

            return {
                "refund_id": refund.id,
                "status": refund.status,
                "amount": self._cents_to_amount(refund.amount),
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating refund: {e}")
            return None

    async def construct_webhook_event(self, payload: str, signature: str) -> Optional[Any]:
        """
        Construct and verify a webhook event

        Args:
            payload: Request body
            signature: Stripe signature header

        Returns:
            Stripe event object or None if verification fails
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            logger.info(f"Webhook event verified: {event['type']}")
            return event

        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.error(f"Error verifying webhook: {e}")
            return None


# Singleton instance
stripe_service = StripeService()

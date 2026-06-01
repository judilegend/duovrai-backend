import logging
import stripe
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.models import Order
from app.types.enums import PlanType

logger = logging.getLogger(__name__)

# Initialize Stripe API Key
stripe.api_key = settings.STRIPE_API_KEY

class StripeService:
    @staticmethod
    def is_mock_enabled() -> bool:
        return (
            not settings.STRIPE_API_KEY 
            or settings.STRIPE_API_KEY.startswith("sk_test_mock")
        )

    def create_checkout_session(self, order: Order) -> dict:
        """
        Creates a Stripe Checkout Session for the specific order.
        """
        if self.is_mock_enabled():
            logger.warning("Stripe is in MOCK mode. Generating mock session.")
            mock_session_id = f"cs_test_{order.id}"
            return {
                "id": mock_session_id,
                "url": f"http://localhost:8000/api/v1/stripe/mock-checkout-success?session_id={mock_session_id}"
            }

        try:
            # Determine correct price ID based on order plan
            price_id = (
                settings.STRIPE_PRICE_PREMIUM 
                if order.plan_type == PlanType.PREMIUM 
                else settings.STRIPE_PRICE_ESSENTIEL
            )
            
            if not price_id:
                raise ValueError("Stripe Price ID is not configured for the selected plan.")

            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    },
                ],
                mode="payment",
                success_url=settings.STRIPE_SUCCESS_URL,
                cancel_url=settings.STRIPE_CANCEL_URL,
                customer_email=order.email,
                metadata={
                    "order_id": order.id
                }
            )
            
            return {
                "id": session.id,
                "url": session.url
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Stripe Gateway Error: {e.user_message or str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Stripe service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Checkout initiation failed: {str(e)}"
            )

    def construct_event(self, payload: bytes, sig_header: str) -> stripe.Event:
        """
        Constructs and verifies a Stripe Webhook Event.
        """
        if self.is_mock_enabled():
            # In mock mode, we assume validation is bypassed, return a mock event payload
            import json
            data = json.loads(payload.decode("utf-8"))
            return stripe.Event.construct_from(data, settings.STRIPE_API_KEY)

        try:
            event = stripe.webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError as e:
            logger.error("Invalid Stripe webhook payload")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError as e:
            logger.error("Invalid Stripe webhook signature verification")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )

stripe_service = StripeService()

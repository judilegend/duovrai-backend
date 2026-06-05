import json
import logging
import stripe
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.models import Order
from app.types.enums import PlanType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Initialize Stripe with the SECRET key (sk_test_… / sk_live_…)
# ---------------------------------------------------------------------------
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------
    @staticmethod
    def is_mock_enabled() -> bool:
        """Returns True when no real Stripe key is configured."""
        return (
            not settings.STRIPE_SECRET_KEY
            or settings.STRIPE_SECRET_KEY.startswith("sk_test_mock")
        )

    # -----------------------------------------------------------------------
    # Checkout Session
    # -----------------------------------------------------------------------
    def create_checkout_session(self, order: Order) -> dict:
        """
        Creates a Stripe Checkout Session for the given order.

        Returns a dict with keys:
            - ``id``  : the Stripe session id  (cs_…)
            - ``url`` : the hosted Checkout URL the user is redirected to
        """
        if self.is_mock_enabled():
            logger.warning("Stripe is in MOCK mode — generating a local mock session.")
            mock_session_id = f"cs_test_{order.id}"
            return {
                "id": mock_session_id,
                "url": (
                    f"http://localhost:8000/api/v1/stripe/mock-checkout-success"
                    f"?session_id={mock_session_id}"
                ),
            }

        try:
            # Resolve the correct Stripe Price ID for the selected plan
            price_id = (
                settings.STRIPE_PRICE_PREMIUM
                if order.plan_type == PlanType.PREMIUM
                else settings.STRIPE_PRICE_ESSENTIEL
            )

            if not price_id:
                raise ValueError(
                    "Stripe Price ID is not configured for the selected plan."
                )

            try:
                # Try creating a standard one-time payment session
                session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[{"price": price_id, "quantity": 1}],
                    mode="payment",
                    success_url=settings.STRIPE_SUCCESS_URL,
                    cancel_url=settings.STRIPE_CANCEL_URL,
                    customer_email=order.email,
                    metadata={"order_id": str(order.id)},
                )
            except stripe.error.StripeError as e:
                # If price is configured as recurring (subscription/recurring), retry in subscription mode
                err_msg = str(e)
                if "recurring price" in err_msg or "subscription" in err_msg:
                    logger.warning("Detected recurring price. Retrying in subscription mode.")
                    session = stripe.checkout.Session.create(
                        payment_method_types=["card"],
                        line_items=[{"price": price_id, "quantity": 1}],
                        mode="subscription",
                        success_url=settings.STRIPE_SUCCESS_URL,
                        cancel_url=settings.STRIPE_CANCEL_URL,
                        customer_email=order.email,
                        metadata={"order_id": str(order.id)},
                    )
                else:
                    raise e

            logger.info(
                f"Stripe Checkout Session created: {session.id} "
                f"for Order {order.id} ({order.plan_type})"
            )
            return {"id": session.id, "url": session.url}

        except stripe.error.StripeError as exc:
            # user_message attribute exists only on some error subclasses
            user_msg = getattr(exc, "user_message", None) or str(exc)
            logger.error(f"Stripe error creating checkout session: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Stripe Gateway Error: {user_msg}",
            )
        except ValueError as exc:
            logger.error(f"Configuration error in Stripe service: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            )
        except Exception as exc:
            logger.exception(f"Unexpected error in StripeService.create_checkout_session: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Checkout initiation failed. Please try again.",
            )

    # -----------------------------------------------------------------------
    # Webhook Event Construction & Signature Verification
    # -----------------------------------------------------------------------
    def construct_event(self, payload: bytes, sig_header: str) -> stripe.Event:
        """
        Validates the Stripe webhook signature and returns the parsed Event.

        Raises HTTPException 400 on invalid payload or forged signature.
        """
        if self.is_mock_enabled():
            # Development convenience: bypass signature check, parse payload directly
            logger.warning(
                "Stripe MOCK mode — skipping webhook signature verification."
            )
            data = json.loads(payload.decode("utf-8"))
            return stripe.Event.construct_from(data, settings.STRIPE_SECRET_KEY)

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event

        except ValueError:
            # Malformed payload (not valid JSON / binary garbage)
            logger.error("Stripe webhook: invalid payload received.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook payload.",
            )
        except stripe.error.SignatureVerificationError:
            # Signature does not match → potential replay/forgery attack
            logger.error("Stripe webhook: signature verification FAILED.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature.",
            )


# Module-level singleton used by the router
stripe_service = StripeService()

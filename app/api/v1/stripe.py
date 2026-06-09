import asyncio
import json
import logging
from fastapi import APIRouter, Depends, Request, Response, BackgroundTasks, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import get_db, SessionLocal
from app.repositories.order_repository import order_repository
from app.repositories.report_repository import report_repository
from app.schemas.schemas import OrderCreate, CheckoutSessionResponse
from app.services.stripe_service import stripe_service
from app.services.claude_service import claude_service
from app.services.pdf_service import pdf_service
from app.services.email_service import email_service
from app.services.ws_manager import broadcast_order_payload
from app.types.enums import OrderStatus, PlanType

logger = logging.getLogger(__name__)
router = APIRouter()

# Background generator pipeline
async def generate_and_email_report_pipeline(order_id: str):
    """
    Executes the long-running pipeline in the background:
    1. Claude API generates the love analysis.
    2. WeasyPrint compiles the HTML and styling to a premium PDF.
    3. Email Service sends the PDF to the customer.
    """
    db = SessionLocal()
    try:
        order = order_repository.get(db, order_id)
        if not order:
            logger.error(f"Background pipeline failed: Order {order_id} not found.")
            return

        logger.info(f"Starting background report generation pipeline for Order {order.id}")

        # 1. Generate text compatibility report from Claude
        report_text = claude_service.generate_love_analysis(order)

        # 2. Render PDF (WeasyPrint or fallback)
        pdf_path = pdf_service.generate_pdf(order, report_text)

        # 3. Create the database record for the report
        report_repository.create(
            db,
            obj_in_data={
                "order_id": order.id,
                "report_content": report_text,
                "pdf_path": pdf_path
            }
        )

        # 4. Email the PDF attachment to the client
        await email_service.send_report_email(
            recipient_email=order.email,
            p1=order.partner1_name,
            p2=order.partner2_name,
            pdf_path=pdf_path
        )

        # 5. Mark order as COMPLETED
        order_repository.update_status(db, order.id, OrderStatus.COMPLETED)
        logger.info(f"Pipeline successfully completed for Order {order.id}")

    except Exception as e:
        logger.exception(f"Fatal error in background pipeline for Order {order_id}: {str(e)}")
        try:
            order_repository.update_status(db, order_id, OrderStatus.FAILED)
        except Exception:
            logger.exception(f"Failed to mark Order {order_id} as FAILED after pipeline error")
    finally:
        db.close()


@router.post("/checkout", response_model=CheckoutSessionResponse)
def create_checkout(order_in: OrderCreate, db: Session = Depends(get_db)):
    """
    Initiates payment process by registering the order and returning Stripe Checkout session.
    """
    try:
        # Determine pricing based on plan type
        amount = 19.90 if order_in.plan_type == PlanType.PREMIUM else 9.90

        # Create Order in PENDING status
        order = order_repository.create(
            db,
            obj_in_data={
                "email": order_in.email,
                "partner1_name": order_in.partner1_name,
                "partner1_birthdate": order_in.partner1_birthdate,
                "partner2_name": order_in.partner2_name,
                "partner2_birthdate": order_in.partner2_birthdate,
                "plan_type": order_in.plan_type,
                "amount": amount,
                "status": OrderStatus.PENDING
            }
        )

        # Generate Stripe session
        session_data = stripe_service.create_checkout_session(order)

        # Update Order with session_id
        order_repository.update(
            db,
            db_obj=order,
            obj_in_data={"stripe_session_id": session_data["id"]}
        )

        return CheckoutSessionResponse(
            checkout_url=session_data["url"],
            session_id=session_data["id"],
            order_id=order.id,
        )

    except Exception as e:
        logger.error(f"Failed to initiate checkout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Checkout creation error: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Receives events from Stripe Checkout. Validates signature and triggers pipeline.
    """
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    if not sig_header and not stripe_service.is_mock_enabled():
        logger.error("Stripe webhook received without Stripe-Signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )

    try:
        # Reconstruct and verify event
        event = stripe_service.construct_event(payload, sig_header)

        if hasattr(event, "to_dict"):
            event_data = event.to_dict()
        elif isinstance(event, dict):
            event_data = event
        else:
            event_data = {}

        event_type = event_data.get("type") if isinstance(event_data, dict) else getattr(event, "type", None)
        logger.info(f"Stripe Webhook event received: {event_type}")

        if event_type == "checkout.session.completed":
            session = event_data.get("data", {}).get("object", {})
            if not session:
                logger.error("Stripe webhook checkout.session.completed missing session object")
                return Response(status_code=400)

            order_id = session.get("metadata", {}).get("order_id")
            stripe_customer_id = session.get("customer")
            
            if order_id:
                logger.info(f"Stripe payment confirmed for Order ID: {order_id}")
                order = order_repository.get(db, order_id)
                if order:
                    order = order_repository.update(
                        db,
                        db_obj=order,
                        obj_in_data={
                            "status": OrderStatus.PAID,
                            "stripe_customer_id": stripe_customer_id
                        }
                    )
                    if order:
                        broadcast_order_payload(order)
                    background_tasks.add_task(generate_and_email_report_pipeline, order_id)
                else:
                    logger.error(f"Stripe event references non-existing Order: {order_id}")
            else:
                logger.error("Stripe Session completed but lacks order_id metadata")
        else:
            logger.info(f"Stripe Webhook event ignored: {event_type}")

        return Response(status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Stripe webhook processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe webhook processing failed"
        )


@router.get("/mock-checkout-success")
async def mock_checkout_success(
    session_id: str, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Developer convenience utility endpoint.
    Simulates a successful Stripe Webhook trigger locally when Stripe Mock Mode is active.
    """
    if not stripe_service.is_mock_enabled():
        return {"error": "Mock mode is inactive. Use Stripe Checkout production tunnel."}

    order = order_repository.get_by_stripe_session_id(db, session_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mock session not found"
        )

    # Transition status: PENDING -> PAID
    order = order_repository.update(
        db,
        db_obj=order,
        obj_in_data={
            "status": OrderStatus.PAID,
            "stripe_customer_id": "cus_mock_12345"
        }
    )

    if order:
        broadcast_order_payload(order)

    # Spawn background generation task
    background_tasks.add_task(generate_and_email_report_pipeline, order.id, db)

    # Redirect to developer check page or return success JSON
    return {
        "message": "Payment simulation successful!",
        "order_id": order.id,
        "status": "PAID",
        "instructions": (
            f"The AI compatibility analysis and PDF report are being generated in the background. "
            f"Use the endpoint '/api/v1/reports/{order.id}' to inspect status and download your report."
        )
    }

import logging
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy.orm import Session
from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models.models import Order, CompatibilityReport
from app.types.enums import OrderStatus, PlanType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_database():
    """
    Seeds the database with three standard orders representing three stages of
    the Duovrai customer flow (PENDING, PAID, COMPLETED) to facilitate immediate frontend testing.
    """
    logger.info("Starting database seeding...")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    try:
        # Check if already seeded
        if db.query(Order).first():
            logger.info("Database already seeded with demo data.")
            return

        # 1. Seed a Pending Order (Unpaid)
        order_pending = Order(
            email="client-pending@example.com",
            partner1_name="Alice",
            partner1_birthdate="1992-04-12",
            partner2_name="Thomas",
            partner2_birthdate="1989-11-23",
            status=OrderStatus.PENDING,
            amount=9.90,
            plan_type=PlanType.ESSENTIEL,
            stripe_session_id="cs_test_pending_order_12345"
        )
        db.add(order_pending)

        # 2. Seed a Paid Order (Processing)
        order_paid = Order(
            email="client-processing@example.com",
            partner1_name="Julien",
            partner1_birthdate="1995-08-05",
            partner2_name="Sarah",
            partner2_birthdate="1996-02-14",
            status=OrderStatus.PAID,
            amount=19.90,
            plan_type=PlanType.PREMIUM,
            stripe_session_id="cs_test_paid_order_67890"
        )
        db.add(order_paid)

        # 3. Seed a Completed Order (Generated and sent)
        order_completed = Order(
            email="client-success@example.com",
            partner1_name="Léo",
            partner1_birthdate="1988-06-30",
            partner2_name="Chloé",
            partner2_birthdate="1990-09-18",
            status=OrderStatus.COMPLETED,
            amount=19.90,
            plan_type=PlanType.PREMIUM,
            stripe_session_id="cs_test_completed_order_55555"
        )
        db.add(order_completed)
        db.flush() # Flush to get order_completed.id for relation

        # Create matching CompatibilityReport
        report = CompatibilityReport(
            order_id=order_completed.id,
            report_content=(
                "# Rapport de Compatibilité Spirituelle & Emotionnelle\n"
                "## Léo & Chloé\n\n"
                "### Chapitre 1 : Introduction et Énergie Initiale du Couple\n"
                "Ce couple représente une harmonie planétaire de type Eau et Feu...\n"
            ),
            pdf_path="C:\\Users\\judi-legend\\.gemini\\antigravity\\scratch\\duovrai-backend\\storage\\reports\\seed_demo.pdf"
        )
        db.add(report)
        
        db.commit()
        logger.info("Database successfully seeded with three testing flows!")
        
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

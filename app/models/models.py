import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from app.database.base import Base
from app.types.enums import OrderStatus, PlanType

class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, index=True)
    
    # Partner 1 info
    partner1_name = Column(String(100), nullable=False)
    partner1_birthdate = Column(String(50), nullable=False) # e.g. "YYYY-MM-DD"
    
    # Partner 2 info
    partner2_name = Column(String(100), nullable=False)
    partner2_birthdate = Column(String(50), nullable=False) # e.g. "YYYY-MM-DD"
    
    # Order Status & details
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    amount = Column(Float, nullable=False)
    plan_type = Column(SQLEnum(PlanType), nullable=False)
    
    # Stripe payment links
    stripe_session_id = Column(String(255), unique=True, index=True, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    report = relationship("CompatibilityReport", back_populates="order", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, email={self.email}, status={self.status})>"


class CompatibilityReport(Base):
    __tablename__ = "compatibility_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Claude AI output content
    report_content = Column(Text, nullable=True)  # Markdown or raw analysis
    
    # WeasyPrint PDF file location
    pdf_path = Column(String(512), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="report")

    def __repr__(self) -> str:
        return f"<CompatibilityReport(id={self.id}, order_id={self.order_id})>"


class Admin(Base):
    __tablename__ = "admins"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Admin(id={self.id}, email={self.email})>"

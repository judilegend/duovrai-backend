from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.types.enums import OrderStatus, PlanType

class OrderCreate(BaseModel):
    email: EmailStr = Field(..., description="Email address to receive the PDF report")
    partner1_name: str = Field(..., min_length=1, max_length=100, description="First name of Partner 1")
    partner1_birthdate: str = Field(..., description="Birthdate of Partner 1 (YYYY-MM-DD)")
    partner2_name: str = Field(..., min_length=1, max_length=100, description="First name of Partner 2")
    partner2_birthdate: str = Field(..., description="Birthdate of Partner 2 (YYYY-MM-DD)")
    plan_type: PlanType = Field(default=PlanType.ESSENTIEL, description="Selected plan (ESSENTIEL: 9,90€ or PREMIUM: 19,90€)")

class OrderResponse(BaseModel):
    id: str
    email: EmailStr
    partner1_name: str
    partner1_birthdate: str
    partner2_name: str
    partner2_birthdate: str
    status: OrderStatus
    amount: float
    plan_type: PlanType
    stripe_session_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str
    order_id: str

class ReportResponse(BaseModel):
    id: str
    order_id: str
    report_content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

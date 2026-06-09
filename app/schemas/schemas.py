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


# Admin Auth Schemas
class AdminLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Admin email address")
    password: str = Field(..., min_length=1, description="Admin password")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class AdminResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class AdminLoginResponse(BaseModel):
    admin: AdminResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class OrderListResponse(BaseModel):
    id: str
    email: str
    partner1_name: str
    partner2_name: str
    status: OrderStatus
    amount: float
    plan_type: PlanType
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Admin Dashboard / Transactions
class TransactionSummary(BaseModel):
    total_orders: int
    total_revenue: float
    orders_pending: int
    orders_completed: int
    orders_failed: int


class OrderDetailResponse(BaseModel):
    id: str
    email: str
    partner1_name: str
    partner2_name: str
    status: OrderStatus
    amount: float
    plan_type: PlanType
    created_at: datetime
    stripe_session_id: Optional[str] = None

    class Config:
        from_attributes = True

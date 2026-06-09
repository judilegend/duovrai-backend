import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Header, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database.session import get_db
from app.models.models import Admin, Order
from app.repositories.admin_repository import admin_repository
from app.repositories.order_repository import order_repository
from app.services.auth_service import auth_service, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schemas.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    TokenResponse,
    AdminResponse,
    TransactionSummary,
    OrderDetailResponse,
)
from app.types.enums import OrderStatus

logger = logging.getLogger(__name__)
router = APIRouter()

from app.services.ws_manager import ws_manager, broadcast_order_payload


def extract_token_from_header(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization[7:]


async def get_current_admin(
    token: str = Depends(extract_token_from_header),
    db: Session = Depends(get_db),
):
    try:
        payload = auth_service.decode_token(token)
        admin_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        admin = admin_repository.get_active_by_id(db, admin_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return admin
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(credentials: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = admin_repository.get_by_email(db, credentials.email)

    if not admin or not auth_service.verify_password(credentials.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive",
        )

    admin.last_login = datetime.utcnow()
    db.commit()

    access_token = auth_service.create_access_token(admin.id)
    refresh_token = auth_service.create_refresh_token(admin.id)

    return AdminLoginResponse(
        admin={
            "id": admin.id,
            "email": admin.email,
            "full_name": admin.full_name,
            "is_active": admin.is_active,
            "created_at": admin.created_at,
            "last_login": admin.last_login,
        },
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = auth_service.decode_token(refresh_token)
        token_type: str = payload.get("type")

        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type for refresh",
            )

        admin_id: str = payload.get("sub")
        admin = admin_repository.get_active_by_id(db, admin_id)

        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found",
            )

        new_access_token = auth_service.create_access_token(admin.id)

        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.get("/me", response_model=AdminResponse)
def get_current_admin_info(current_admin: Admin = Depends(get_current_admin)):
    return current_admin


@router.get("/orders", response_model=dict)
def get_admin_orders(
    status_filter: OrderStatus = Query(None, description="Filter by order status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Order).order_by(desc(Order.created_at))

    if status_filter:
        query = query.filter(Order.status == status_filter)

    total = query.count()
    orders = query.offset(skip).limit(limit).all()

    pending_count = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
    paid_count = db.query(Order).filter(Order.status == OrderStatus.PAID).count()
    completed_count = db.query(Order).filter(Order.status == OrderStatus.COMPLETED).count()
    failed_count = db.query(Order).filter(Order.status == OrderStatus.FAILED).count()

    return {
        "orders": [
            {
                "id": o.id,
                "email": o.email,
                "partner1_name": o.partner1_name,
                "partner2_name": o.partner2_name,
                "status": o.status,
                "amount": o.amount,
                "plan_type": o.plan_type,
                "created_at": o.created_at,
                "updated_at": o.updated_at,
            }
            for o in orders
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
        "metrics": {
            "total_orders": total,
            "total_revenue": float(sum([o.amount for o in db.query(Order).all()]) or 0.0),
            "pending": pending_count,
            "paid": paid_count,
            "completed": completed_count,
            "failed": failed_count,
            "total": pending_count + paid_count + completed_count + failed_count,
        },
    }


@router.websocket("/orders/ws")
async def admin_order_updates_websocket(
    websocket: WebSocket,
    token: str | None = Query(None),
    db: Session = Depends(get_db),
):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = auth_service.decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        admin_id: str = payload.get("sub")
        current_admin = admin_repository.get_active_by_id(db, admin_id)
        if not current_admin:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await ws_manager.connect(websocket)
        await websocket.send_json({"type": "connected", "message": "Realtime order updates enabled."})

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    except Exception:
        ws_manager.disconnect(websocket)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.get("/orders/{order_id}")
def get_admin_order_detail(
    order_id: str,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    order = order_repository.get(db, order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    return {
        "id": order.id,
        "email": order.email,
        "partner1_name": order.partner1_name,
        "partner1_birthdate": order.partner1_birthdate,
        "partner2_name": order.partner2_name,
        "partner2_birthdate": order.partner2_birthdate,
        "status": order.status,
        "amount": order.amount,
        "plan_type": order.plan_type,
        "stripe_session_id": order.stripe_session_id,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


@router.patch("/orders/{order_id}/status")
def update_order_status(
    order_id: str,
    new_status: OrderStatus,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    order = order_repository.get(db, order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    old_status = order.status
    updated_order = order_repository.update_status(db, order_id, new_status)

    logger.info(
        f"Admin {current_admin.email} updated order {order_id} status from {old_status} to {new_status}"
    )

    if updated_order:
        broadcast_order_payload(updated_order)

    return {
        "order_id": order_id,
        "old_status": old_status,
        "new_status": updated_order.status if updated_order else old_status,
        "updated_at": datetime.utcnow(),
    }


# Dashboard Summary
@router.get("/dashboard/summary", response_model=TransactionSummary)
def get_dashboard_summary(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Get dashboard summary stats. Requires valid JWT token.
    """
    total_orders = db.query(Order).count()
    total_revenue = sum([o.amount for o in db.query(Order).all()]) or 0.0
    orders_pending = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
    orders_completed = db.query(Order).filter(Order.status == OrderStatus.COMPLETED).count()
    orders_failed = db.query(Order).filter(Order.status == OrderStatus.FAILED).count()

    return TransactionSummary(
        total_orders=total_orders,
        total_revenue=total_revenue,
        orders_pending=orders_pending,
        orders_completed=orders_completed,
        orders_failed=orders_failed
    )


# Get Orders by Status
@router.get("/transactions", response_model=list[OrderDetailResponse])
def get_transactions(
    status: str = None,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Get transactions. Filter by status if provided (pending, completed, failed).
    Requires valid JWT token.
    """
    query = db.query(Order)

    if status:
        status_upper = status.upper()
        if status_upper not in [s.name for s in OrderStatus]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join([s.name for s in OrderStatus])}"
            )
        query = query.filter(Order.status == OrderStatus[status_upper])

    orders = query.order_by(Order.created_at.desc()).all()
    return orders


# Get Orders by Status (Alternative - using path parameter)
@router.get("/transactions/status/{payment_status}", response_model=list[OrderDetailResponse])
def get_transactions_by_status(
    payment_status: str,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Get transactions by status (pending, completed, failed).
    Example: /api/v1/admin/transactions/status/pending
    """
    status_upper = payment_status.upper()
    if status_upper not in [s.name for s in OrderStatus]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join([s.name for s in OrderStatus])}"
        )

    orders = (
        db.query(Order)
        .filter(Order.status == OrderStatus[status_upper])
        .order_by(Order.created_at.desc())
        .all()
    )
    return orders

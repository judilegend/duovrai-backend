from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import Order
from app.repositories.base import BaseRepository
from app.types.enums import OrderStatus

class OrderRepository(BaseRepository[Order]):
    def __init__(self):
        super().__init__(Order)

    def get_by_stripe_session_id(self, db: Session, stripe_session_id: str) -> Optional[Order]:
        return db.query(self.model).filter(self.model.stripe_session_id == stripe_session_id).first()

    def update_status(self, db: Session, order_id: str, status: OrderStatus) -> Optional[Order]:
        order = self.get(db, order_id)
        if order:
            order.status = status
            db.add(order)
            db.commit()
            db.refresh(order)
        return order

order_repository = OrderRepository()

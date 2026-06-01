from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import CompatibilityReport
from app.repositories.base import BaseRepository

class ReportRepository(BaseRepository[CompatibilityReport]):
    def __init__(self):
        super().__init__(CompatibilityReport)

    def get_by_order_id(self, db: Session, order_id: str) -> Optional[CompatibilityReport]:
        return db.query(self.model).filter(self.model.order_id == order_id).first()

report_repository = ReportRepository()

from sqlalchemy.orm import Session
from app.models.models import Admin
from app.repositories.base import BaseRepository


class AdminRepository(BaseRepository):
    def get_by_email(self, db: Session, email: str):
        return db.query(Admin).filter(Admin.email == email).first()

    def get_active_by_id(self, db: Session, admin_id: str):
        return db.query(Admin).filter(
            Admin.id == admin_id,
            Admin.is_active == True
        ).first()


admin_repository = AdminRepository(Admin)

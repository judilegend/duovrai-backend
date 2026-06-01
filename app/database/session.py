from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.core.config import settings

# If using SQLite, we need to allow multiple threads to access it (FastAPI is multithreaded/async)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Dependency to get db session in FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

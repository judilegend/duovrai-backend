import os
import sys
# Ensure project root is on sys.path so `import app` works when running the script directly
_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.database.session import SessionLocal, engine
from app.models.models import CompatibilityReport, Order
from app.core.config import settings


def resolve_path(raw_path: str) -> str:
    if not raw_path:
        return ""
    if os.path.isabs(raw_path):
        return raw_path
    # Try resolving relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate = os.path.abspath(os.path.join(project_root, raw_path))
    if os.path.exists(candidate):
        return candidate
    # fallback: resolve relative to configured PDF_OUTPUT_DIR
    candidate2 = os.path.abspath(os.path.join(settings.PDF_OUTPUT_DIR, os.path.basename(raw_path)))
    return candidate2


def main():
    print("Using DATABASE_URL:", settings.DATABASE_URL)
    db = SessionLocal()
    try:
        reports = db.query(CompatibilityReport).all()
        if not reports:
            print("No CompatibilityReport rows found in DB.")
            return

        print(f"Found {len(reports)} report rows:\n")
        for r in reports:
            raw = r.pdf_path or ""
            resolved = resolve_path(raw)
            exists = os.path.exists(resolved) if resolved else False
            order = db.query(Order).filter(Order.id == r.order_id).first()
            email = order.email if order else "(no order)"
            print("-"*60)
            print(f"Report ID : {r.id}")
            print(f"Order ID  : {r.order_id}")
            print(f"Email     : {email}")
            print(f"Raw path  : {raw}")
            print(f"Resolved  : {resolved}")
            print(f"Exists    : {exists}")
        print("\nScan complete.")
    finally:
        db.close()


if __name__ == '__main__':
    main()

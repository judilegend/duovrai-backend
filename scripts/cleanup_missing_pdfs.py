import sys
import os

_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.database.session import SessionLocal
from app.models.models import CompatibilityReport

def main():
    db = SessionLocal()
    try:
        # Find and nullify pdf_path entries for seed_demo.pdf
        reports = db.query(CompatibilityReport).filter(
            CompatibilityReport.pdf_path.like('%seed_demo.pdf%')
        ).all()
        
        if not reports:
            print("No seed_demo.pdf entries found.")
            return
        
        for r in reports:
            print(f"Clearing pdf_path for Report {r.id}: {r.pdf_path}")
            r.pdf_path = None
        
        db.commit()
        print(f"✓ Updated {len(reports)} entries.")
    finally:
        db.close()

if __name__ == '__main__':
    main()

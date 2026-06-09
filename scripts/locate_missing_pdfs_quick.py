import os
import sys

# Ensure project root on sys.path
_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.database.session import SessionLocal
from app.models.models import CompatibilityReport
from app.core.config import settings

# Quick search roots (project + common user folders)
user = os.path.expanduser('~')
SEARCH_ROOTS = [
    _project_root,
    os.path.join(user, 'Desktop'),
    os.path.join(user, 'Downloads'),
    os.path.join(user, 'Documents'),
    os.path.join(user, 'Pictures'),
]


def find_file_in_roots(filename):
    matches = []
    for root in SEARCH_ROOTS:
        if not root or not os.path.exists(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            if filename in filenames:
                matches.append(os.path.join(dirpath, filename))
    return matches


def main():
    print('Quick scan roots:', SEARCH_ROOTS)
    db = SessionLocal()
    try:
        reports = db.query(CompatibilityReport).all()
        missing = []
        for r in reports:
            raw = r.pdf_path or ''
            if raw and os.path.exists(raw):
                continue
            if raw:
                missing.append((r.id, r.order_id, raw))
        if not missing:
            print('No missing PDF entries.')
            return
        for rid, oid, raw in missing:
            basename = os.path.basename(raw)
            print('\nSearching for', basename)
            matches = find_file_in_roots(basename)
            if matches:
                print('Found:')
                for m in matches:
                    print('  ', m)
            else:
                print('No matches in quick roots.')
    finally:
        db.close()

if __name__ == '__main__':
    main()

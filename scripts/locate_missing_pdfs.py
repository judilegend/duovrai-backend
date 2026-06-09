import os
import sys

# Ensure project root on sys.path so `import app` works when running script
_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Now import application modules
from app.database.session import SessionLocal
from app.models.models import CompatibilityReport
from app.core.config import settings

SEARCH_ROOTS = [
    _project_root,  # workspace project root
    os.path.expanduser('~'),  # user home directory
]


def find_file_in_roots(filename):
    matches = []
    for root in SEARCH_ROOTS:
        for dirpath, dirnames, filenames in os.walk(root):
            if filename in filenames:
                matches.append(os.path.join(dirpath, filename))
    return matches


def main():
    print('Scanning DB for missing PDF entries...')
    db = SessionLocal()
    try:
        reports = db.query(CompatibilityReport).all()
        missing = []
        for r in reports:
            raw = r.pdf_path or ''
            # if exists on disk, skip
            if raw and os.path.exists(raw):
                continue
            if raw:
                missing.append((r.id, r.order_id, raw))

        if not missing:
            print('No missing PDF entries found in DB.')
            return

        print(f'Found {len(missing)} missing entries. Searching for files in roots: {SEARCH_ROOTS}\n')
        for rid, oid, raw in missing:
            basename = os.path.basename(raw)
            print('-'*60)
            print(f'Report ID: {rid}')
            print(f'Order ID : {oid}')
            print(f'Expected : {raw}')
            print(f'Basename : {basename}')
            matches = find_file_in_roots(basename)
            if matches:
                print('Matches found:')
                for m in matches:
                    print('  ', m)
            else:
                print('No matches found in search roots.')
        print('\nSearch complete.')
    finally:
        db.close()

if __name__ == '__main__':
    main()

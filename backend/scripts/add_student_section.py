import sqlite3
import os
DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'erp.db'))
print('DB file:', DB)
conn = sqlite3.connect(DB)
c = conn.cursor()
# check if column exists
c.execute("PRAGMA table_info('students')")
cols = [r[1] for r in c.fetchall()]
print('Students columns:', cols)
if 'section' not in cols:
    print('Adding section column to students table')
    c.execute("ALTER TABLE students ADD COLUMN section TEXT DEFAULT 'A'")
    conn.commit()
    # Backfill with 'A' if null
    c.execute("UPDATE students SET section = 'A' WHERE section IS NULL")
    conn.commit()
    print('section column added and backfilled')
else:
    print('section column already present')
conn.close()

import sqlite3
import os

DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'erp.db'))
print('DB file:', DB)
conn = sqlite3.connect(DB)
c = conn.cursor()

# Check teachers table for password_hash
c.execute("PRAGMA table_info('teachers')")
cols = [r[1] for r in c.fetchall()]
print('Teachers columns:', cols)
if 'password_hash' not in cols:
    print('Adding column teachers.password_hash')
    c.execute("ALTER TABLE teachers ADD COLUMN password_hash TEXT")

conn.commit()
conn.close()
print('Done')

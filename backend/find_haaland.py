from app.db.database import SessionLocal
from sqlalchemy import text
from verify_database import _load_env
_load_env()

db = SessionLocal()
res = db.execute(text("SELECT id, name FROM players WHERE name ILIKE '%haaland%'")).fetchall()
print(res)

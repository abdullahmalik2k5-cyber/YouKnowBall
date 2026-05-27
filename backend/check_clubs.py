from app.db.database import SessionLocal
from sqlalchemy import text
from verify_database import _load_env
_load_env()

db = SessionLocal()
res = db.execute(text("SELECT name FROM clubs WHERE name ILIKE '%united%' OR name ILIKE '%barcelona%'")).fetchall()
print([r[0] for r in res])

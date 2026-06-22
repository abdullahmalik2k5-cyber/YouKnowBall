import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from verify_database import _load_env
_load_env()
from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
rows = db.execute(text(
    "SELECT name, position, sub_position, position_group FROM players WHERE LOWER(name) LIKE '%saliba%'"
)).fetchall()
print("Saliba rows:", rows)

# Also check distinct position_group values in the DB
distinct = db.execute(text("SELECT DISTINCT position_group FROM players LIMIT 30")).fetchall()
print("Distinct position_groups:", distinct)
db.close()

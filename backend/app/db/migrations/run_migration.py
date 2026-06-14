import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from app.db.database import engine

def run_migration():
    columns_to_add = [
        ("positions", "VARCHAR(100)", "NULL"),
        ("born", "INTEGER", "NULL"),
        ("minutes", "INTEGER", "NULL"),
        ("matches", "INTEGER", "NULL"),
        ("goals", "INTEGER", "NULL"),
        ("assists", "INTEGER", "NULL"),
        ("is_gk", "BOOLEAN", "DEFAULT FALSE"),
        ("difficulty", "VARCHAR(20)", "NULL"),
        ("eligible", "BOOLEAN", "DEFAULT TRUE"),
        ("region", "VARCHAR(60)", "NULL"),
        ("city", "VARCHAR(100)", "NULL"),
        ("big_club", "BOOLEAN", "DEFAULT FALSE"),
        ("is_starter", "BOOLEAN", "DEFAULT FALSE"),
        ("is_supersub", "BOOLEAN", "DEFAULT FALSE"),
        ("is_everpresent", "BOOLEAN", "DEFAULT FALSE"),
        ("goals_bracket", "VARCHAR(20)", "NULL"),
        ("assists_bracket", "VARCHAR(20)", "NULL"),
        ("double_double", "BOOLEAN", "DEFAULT FALSE"),
        ("penalty_taker", "BOOLEAN", "DEFAULT FALSE"),
        ("sent_off", "BOOLEAN", "DEFAULT FALSE"),
        ("scored_own_goal", "BOOLEAN", "DEFAULT FALSE"),
        ("discipline", "VARCHAR(20)", "NULL"),
        ("heavily_booked", "BOOLEAN", "DEFAULT FALSE"),
        ("big_crosser", "BOOLEAN", "DEFAULT FALSE"),
        ("ball_winner", "BOOLEAN", "DEFAULT FALSE"),
        ("gets_fouled", "BOOLEAN", "DEFAULT FALSE"),
        ("shoots_a_lot", "BOOLEAN", "DEFAULT FALSE"),
        ("gk_clean_sheets", "INTEGER", "DEFAULT 0"),
        ("gk_strong", "BOOLEAN", "DEFAULT FALSE"),
        ("high_ppm", "BOOLEAN", "DEFAULT FALSE")
    ]

    print("Starting database migration to extend players table...")
    with engine.begin() as conn:
        for col_name, col_type, col_default in columns_to_add:
            sql = f"ALTER TABLE players ADD COLUMN IF NOT EXISTS {col_name} {col_type} {col_default};"
            print(f"Executing: {sql}")
            conn.execute(text(sql))
    print("Database migration completed successfully!")

if __name__ == "__main__":
    run_migration()

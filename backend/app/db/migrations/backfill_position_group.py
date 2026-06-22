"""
Fast bulk backfill: sets position_group for all players where it is NULL or 'UNKNOWN',
using a single CASE expression UPDATE — no Python loop needed.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from verify_database import _load_env
_load_env()

from app.db.database import engine
from sqlalchemy import text

SQL = """
UPDATE players
SET position_group = CASE
    -- Broad Transfermarkt categories (players.position column)
    WHEN position = 'Goalkeeper'  THEN 'GK'
    WHEN position = 'Defender'    THEN 'DEF'
    WHEN position = 'Midfield'    THEN 'MID'
    WHEN position = 'Attack'      THEN 'ATK'
    -- Sub-position fallbacks (players.sub_position column)
    WHEN sub_position IN ('Centre-Back','Left-Back','Right-Back','Wing-Back','Left Wing-Back','Right Wing-Back') THEN 'DEF'
    WHEN sub_position IN ('Defensive Midfield','Central Midfield','Attacking Midfield','Right Midfield','Left Midfield') THEN 'MID'
    WHEN sub_position IN ('Left Winger','Right Winger','Centre-Forward','Second Striker','Striker') THEN 'ATK'
    WHEN sub_position = 'Goalkeeper' THEN 'GK'
    ELSE position_group  -- leave unchanged if we can't map
END
WHERE position_group IS NULL OR UPPER(COALESCE(position_group, '')) = 'UNKNOWN';
"""

def run():
    with engine.begin() as conn:
        result = conn.execute(text(SQL))
        print(f"Backfill complete. Rows updated: {result.rowcount}")

if __name__ == "__main__":
    run()

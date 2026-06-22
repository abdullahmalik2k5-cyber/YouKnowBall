"""Quick regression test for the two bugs."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from verify_database import _load_env
_load_env()

from app.db.database import SessionLocal
from app.game.queries import handlers
from sqlalchemy import text

db = SessionLocal()

# Find Saliba's player ID
row = db.execute(text("SELECT id, name, position, sub_position, position_group FROM players WHERE LOWER(name) LIKE '%saliba%'")).fetchone()
if not row:
    print("[FAIL] Saliba not found!")
    db.close()
    sys.exit(1)

saliba_id = str(row[0])
print(f"[OK] Found: {row[1]} | position='{row[2]}' | sub_position='{row[3]}' | position_group='{row[4]}'")
print()

# Test Bug 2 fix: position handler
print("=== BUG 2: Position Handler Test ===")
all_ok = True
for pos in ["GK", "DEF", "MID", "ATK"]:
    answer, fact = handlers.handle_position(db, saliba_id, pos)
    expected = "YES" if pos == "DEF" else "NO"
    ok = answer == expected
    if not ok:
        all_ok = False
    marker = "[OK]" if ok else "[FAIL]"
    print(f"  {marker} {pos}: {answer} (expected {expected}) - {fact}")

print()

# Test Bug 1 fix: big_six handler  
print("=== BUG 1: Big Six Handler Test ===")
answer, fact = handlers.handle_big_six(db, saliba_id)
ok = answer == "YES"
print(f"  {'[OK]' if ok else '[FAIL]'} big_six: {answer} (expected YES) - {fact}")

print()

# Test the NLP parser recognizes "big 6" questions
print("=== NLP Parser Test ===")
from app.nlp.regex_patterns import parse_with_rules
tests = [
    "is he in the big 6",
    "does he play for a big six club",
    "big 6 player?",
    "is he a big-six player",
]
for q in tests:
    result = parse_with_rules(db, q)
    ok = result is not None and result.get("type") == "big_six"
    print(f"  {'[OK]' if ok else '[FAIL]'} '{q}' -> {result}")

db.close()
print("\nDone.")

"""Final verification of all fixes."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from verify_database import _load_env
_load_env()

from app.db.database import SessionLocal
from app.game.queries import handlers
from app.nlp.regex_patterns import parse_with_rules
from sqlalchemy import text

db = SessionLocal()

# ===== DB Backfill =====
print("=== Fix 1: DB position_group backfill ===")
row = db.execute(text(
    "SELECT name, position, sub_position, position_group FROM players WHERE LOWER(name) LIKE '%saliba%'"
)).fetchone()
print(f"  Saliba: position_group='{row[3]}' (expected DEF)")
assert row[3] == "DEF", f"FAIL: got {row[3]}"

# Count remaining UNKNOWNs
unknown_count = db.execute(text(
    "SELECT COUNT(*) FROM players WHERE UPPER(COALESCE(position_group,'')) = 'UNKNOWN' OR position_group IS NULL"
)).scalar()
print(f"  Remaining UNKNOWN/NULL position_group rows: {unknown_count}")
print()

# ===== Position handler =====
saliba_id = str(db.execute(text(
    "SELECT id FROM players WHERE LOWER(name) LIKE '%saliba%'"
)).scalar())

print("=== Fix 2: Position handler (Saliba) ===")
for pos in ["GK", "DEF", "MID", "ATK"]:
    answer, fact = handlers.handle_position(db, saliba_id, pos)
    expected = "YES" if pos == "DEF" else "NO"
    ok = answer == expected
    print(f"  {'[OK]' if ok else '[FAIL]'} {pos}: {answer} (expected {expected})")
print()

# ===== Big six handler =====
print("=== Fix 1b: Big six handler (Saliba) ===")
answer, fact = handlers.handle_big_six(db, saliba_id)
print(f"  {'[OK]' if answer=='YES' else '[FAIL]'} big_six: {answer} (expected YES)")
print(f"  Fact: {fact}")
print()

# ===== NLP parser big_six ===
print("=== Fix 4: NLP big_six parsing ===")
for q in ["is he in the big 6", "big six player?", "big-six club", "does he play for the big 6"]:
    result = parse_with_rules(db, q)
    ok = result is not None and result.get("type") == "big_six"
    print(f"  {'[OK]' if ok else '[FAIL]'} '{q}' -> {result}")
print()

# ===== Explainer censor test =====
print("=== Fix 3: Explainer censor (short name parts) ===")
import re
# Simulate what explainer does for "Son Heung-min"
player_name = "Son Heung-min"
explanation = "No, Son has never played for that club."
STOP_WORDS = {
    "de", "van", "le", "la", "da", "di", "do", "el", "al",
    "bin", "bel", "del", "den", "von", "der", "des", "du",
    "the", "and", "for", "in", "of", "at", "to",
}
player_name_lower = player_name.lower()
if player_name_lower in explanation.lower():
    explanation = re.compile(re.escape(player_name), re.IGNORECASE).sub("the player", explanation)
else:
    parts = [p for p in player_name.split() if p.lower() not in STOP_WORDS]
    for part in parts:
        if part.lower() in explanation.lower():
            explanation = re.compile(re.escape(part), re.IGNORECASE).sub("the player", explanation)
ok = "Son" not in explanation
print(f"  {'[OK]' if ok else '[FAIL]'} Censored: '{explanation}'")
print()

db.close()
print("All checks done.")

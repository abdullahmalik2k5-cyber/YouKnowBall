"""Query handlers — map validated NLP intent directly to SQL queries.

Each handler takes a database session, the hidden player's ID, and the
relevant entity value(s). It returns "YES", "NO", or "UNKNOWN".

New handlers (continent, age, foot) added alongside the original 5.
"""
from __future__ import annotations

from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import Session

# Country → continent mapping (mirrors engine.py COUNTRY_TO_CONTINENT)
# Imported here to avoid circular imports with the engine module.
from app.game.candidate_engine.engine import COUNTRY_TO_CONTINENT


# ─── Original handlers ────────────────────────────────────────────────────────

def handle_nationality(db: Session, player_id: str, country_name: str) -> tuple[str, str]:
    """Check if the player is of the given nationality. Returns (answer, fact_details)."""
    query = text("""
        SELECT c.name
        FROM players p
        JOIN countries c ON p.nationality_id = c.id
        WHERE p.id = :pid
    """)
    result = db.execute(query, {"pid": player_id}).scalar()
    if not result:
        return "UNKNOWN", "No nationality data found."

    asked = country_name.strip().lower()
    actual = result.strip().lower()

    # Strict exact equality only — bidirectional substring matching causes false positives:
    # e.g. 'Iran' inside 'Ukraine', 'Mali' inside 'Somalia', 'Niger' inside 'Nigeria',
    # 'Oman' inside 'Romania', 'Guinea' inside 'Equatorial Guinea'.
    # The NLP layer always returns a canonical country name, so exact match is correct.
    answer = "YES" if asked == actual else "NO"
    fact = f"His nationality is {result}." if answer == "YES" else f"His nationality is not {country_name} — it is {result}."
    return answer, fact


def handle_current_club(db: Session, player_id: str, club_name: str) -> tuple[str, str]:
    """Check if the player currently plays for the given club."""
    query = text("""
        SELECT c.name
        FROM players p
        JOIN clubs c ON p.current_club_id = c.id
        WHERE p.id = :pid
    """)
    result = db.execute(query, {"pid": player_id}).scalar()
    if not result:
        return "UNKNOWN", "No current club data found."

    # Use bidirectional substring for club names — this is intentional because club
    # canonical names can differ from common names (e.g. "Futbol Club Barcelona" vs "Barcelona").
    # However, require the shorter string to be at least 4 chars to avoid false positives.
    asked = club_name.strip().lower()
    actual = result.strip().lower()
    if len(asked) >= 4 and (asked in actual or actual in asked):
        match = True
    elif asked == actual:
        match = True
    else:
        match = False

    answer = "YES" if match else "NO"
    fact = f"His current club is {result}." if answer == "YES" else f"His current club is not {club_name}."
    return answer, fact


def handle_club_history(db: Session, player_id: str, club_name: str) -> tuple[str, str]:
    """Check if the player has ever played for the given club."""
    query = text("""
        SELECT COUNT(*), MAX(c.name)
        FROM player_club_history pch
        JOIN clubs c ON pch.club_id = c.id
        WHERE pch.player_id = :pid AND LOWER(c.name) LIKE :club
    """)
    row = db.execute(query, {"pid": player_id, "club": f"%{club_name.lower()}%"}).fetchone()
    count, club_full = (row[0] or 0), (row[1] or club_name)
    answer = "YES" if count > 0 else "NO"
    fact = f"He has played for {club_full} in his career." if answer == "YES" else f"He has never played for {club_name}."
    return answer, fact


def handle_position(db: Session, player_id: str, position_group: str) -> tuple[str, str]:
    """Check if the player plays in a specific position group."""
    query = text("""
        SELECT position_group, position, sub_position
        FROM players
        WHERE id = :pid
    """)
    row = db.execute(query, {"pid": player_id}).fetchone()
    if not row or (not row[0] and not row[1]):
        return "UNKNOWN", "No position data found."

    pos_group, raw_position, sub_pos = row[0], row[1], row[2]

    # Map from Transfermarkt broad position names → our 4-code groups
    # Covers the case where position_group is UNKNOWN/null in the DB
    BROAD_TO_GROUP = {
        "goalkeeper": "GK",
        "defender": "DEF",
        "midfield": "MID",
        "attack": "ATK",
    }
    # Also map sub-positions for finer accuracy
    SUB_TO_GROUP = {
        "goalkeeper": "GK",
        "centre-back": "DEF", "left-back": "DEF", "right-back": "DEF",
        "wing-back": "DEF", "left wing-back": "DEF", "right wing-back": "DEF",
        "defensive midfield": "MID", "central midfield": "MID",
        "attacking midfield": "MID", "right midfield": "MID", "left midfield": "MID",
        "left winger": "ATK", "right winger": "ATK", "centre-forward": "ATK",
        "second striker": "ATK", "striker": "ATK",
    }

    # Determine the effective position group
    effective_group = None
    if pos_group and pos_group.upper() not in ("UNKNOWN", ""):
        effective_group = pos_group.upper()
    elif sub_pos:
        effective_group = SUB_TO_GROUP.get(sub_pos.lower())
    if not effective_group and raw_position:
        effective_group = BROAD_TO_GROUP.get(raw_position.lower())

    if not effective_group:
        return "UNKNOWN", "No position data found."

    answer = "YES" if effective_group == position_group.upper() else "NO"
    pos_label_map = {"GK": "Goalkeeper", "DEF": "Defender", "MID": "Midfielder", "ATK": "Attacker"}
    asked_label = pos_label_map.get(position_group.upper(), position_group)
    if answer == "YES":
        fact = f"His position is {asked_label}" + (f" ({sub_pos})." if sub_pos else ".")
    else:
        actual_label = pos_label_map.get(effective_group, effective_group)
        fact = f"He is not a {asked_label} — he is a {actual_label}."
    return answer, fact



def handle_competition_history(db: Session, player_id: str, competition_name: str) -> tuple[str, str]:
    """Check if the player has ever appeared in the given competition."""
    query = text("""
        SELECT COUNT(*), MAX(c.name)
        FROM appearances a
        JOIN competitions c ON a.competition_id = c.id
        WHERE a.player_id = :pid AND LOWER(c.name) LIKE :comp
    """)
    row = db.execute(query, {"pid": player_id, "comp": f"%{competition_name.lower()}%"}).fetchone()
    count, comp_full = (row[0] or 0), (row[1] or competition_name)
    answer = "YES" if count > 0 else "NO"
    fact = f"He has played in the {comp_full}." if answer == "YES" else f"He has never played in the {competition_name}."
    return answer, fact


def handle_big_six(db: Session, player_id: str) -> tuple[str, str]:
    """Check if the player has ever played for one of the 'Big Six' Premier League clubs.

    The Big Six: Arsenal, Chelsea, Liverpool, Manchester City,
                 Manchester United, Tottenham Hotspur.
    We match using a broad LIKE on club name so canonical DB names
    (e.g. 'Manchester City Football Club') are covered.
    """
    BIG_SIX_PATTERNS = [
        "%arsenal%",
        "%chelsea%",
        "%liverpool%",
        "%manchester city%",
        "%manchester united%",
        "%tottenham%",
    ]
    for pattern in BIG_SIX_PATTERNS:
        row = db.execute(
            text("""
                SELECT COUNT(*)
                FROM player_club_history pch
                JOIN clubs c ON pch.club_id = c.id
                WHERE pch.player_id = :pid AND LOWER(c.name) LIKE :club
            """),
            {"pid": player_id, "club": pattern}
        ).fetchone()
        if row and row[0] > 0:
            # Find the actual club name for the fact message
            club_name_row = db.execute(
                text("""
                    SELECT MAX(c.name)
                    FROM player_club_history pch
                    JOIN clubs c ON pch.club_id = c.id
                    WHERE pch.player_id = :pid AND LOWER(c.name) LIKE :club
                """),
                {"pid": player_id, "club": pattern}
            ).fetchone()
            club_display = club_name_row[0] if club_name_row else "a Big Six club"
            return "YES", f"Yes — he has played for {club_display}, which is one of the Big Six."

    return "NO", "He has never played for any of the Big Six Premier League clubs (Arsenal, Chelsea, Liverpool, Man City, Man United, Spurs)."


# ─── New handlers ─────────────────────────────────────────────────────────────


def handle_continent(db: Session, player_id: str, continent_name: str) -> tuple[str, str]:
    """
    Check if the player is from the given continent.
    Uses the COUNTRY_TO_CONTINENT map and falls back to the DB confederation column.
    """
    query = text("""
        SELECT c.name, COALESCE(c.confederation, '') AS confederation
        FROM players p
        JOIN countries c ON p.nationality_id = c.id
        WHERE p.id = :pid
    """)
    row = db.execute(query, {"pid": player_id}).fetchone()
    if not row:
        return "UNKNOWN", "No nationality data found."

    country_name, confederation = row[0], row[1]

    # Primary: use static map
    player_continent = COUNTRY_TO_CONTINENT.get(country_name)

    # Fallback: use DB confederation field
    if not player_continent:
        conf_to_continent = {
            "UEFA": "Europe", "CONMEBOL": "South America",
            "CONCACAF": "North America", "CAF": "Africa",
            "AFC": "Asia", "OFC": "Oceania",
        }
        player_continent = conf_to_continent.get(confederation.upper().strip())

    if not player_continent:
        return "UNKNOWN", f"Could not determine the continent for {country_name}."

    target = continent_name.strip().title()
    # Handle "South America" title-casing edge case
    if continent_name.lower() == "south america":
        target = "South America"
    elif continent_name.lower() == "north america":
        target = "North America"

    answer = "YES" if player_continent == target else "NO"
    if answer == "YES":
        fact = f"He is from {country_name}, which is in {player_continent}."
    else:
        fact = f"He is from {country_name} ({player_continent}), not {target}."
    return answer, fact


def handle_age(db: Session, player_id: str, operator: str, years: int) -> tuple[str, str]:
    """
    Check if the player meets the age condition.
    Uses the pre-computed `age` column, with `date_of_birth` as a fallback.
    """
    # First try the pre-stored age column
    row = db.execute(
        text("SELECT age, date_of_birth FROM players WHERE id = :pid"),
        {"pid": player_id}
    ).fetchone()

    if not row:
        return "UNKNOWN", "Player not found."

    stored_age, dob = row[0], row[1]

    # Compute age from date_of_birth if stored age is missing
    if stored_age is None and dob:
        today = date.today()
        stored_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    if stored_age is None:
        return "UNKNOWN", "Age data not available for this player."

    op_funcs = {
        "lt": lambda a, y: a < y,
        "lte": lambda a, y: a <= y,
        "gt": lambda a, y: a > y,
        "gte": lambda a, y: a >= y,
        "eq": lambda a, y: a == y,
    }
    op_labels = {
        "lt": f"under {years}",
        "lte": f"{years} or younger",
        "gt": f"older than {years}",
        "gte": f"at least {years}",
        "eq": f"exactly {years}",
    }

    check = op_funcs.get(operator, lambda a, y: a < y)
    result = check(stored_age, years)
    answer = "YES" if result else "NO"
    label = op_labels.get(operator, f"{operator} {years}")

    if answer == "YES":
        fact = f"He is {stored_age} years old, which is {label}."
    else:
        fact = f"He is {stored_age} years old — not {label}."
    return answer, fact


def handle_foot(db: Session, player_id: str, foot_value: str) -> tuple[str, str]:
    """Check the player's preferred foot."""
    result = db.execute(
        text("SELECT preferred_foot FROM players WHERE id = :pid"),
        {"pid": player_id}
    ).scalar()

    if result is None:
        return "UNKNOWN", "Preferred foot data is not available for this player."

    answer = "YES" if result.lower() == foot_value.lower() else "NO"
    if answer == "YES":
        fact = f"He is {foot_value}-footed."
    else:
        fact = f"He is not {foot_value}-footed — he prefers his {result.lower()} foot."
    return answer, fact

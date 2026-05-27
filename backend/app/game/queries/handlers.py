"""Query handlers to map user intent directly to SQL queries."""
from sqlalchemy import text
from sqlalchemy.orm import Session

def handle_nationality(db: Session, player_id: str, country_name: str) -> str:
    """Check if the player is of the given nationality."""
    query = text("""
        SELECT c.name
        FROM players p
        JOIN countries c ON p.nationality_id = c.id
        WHERE p.id = :pid
    """)
    result = db.execute(query, {"pid": player_id}).scalar()
    if not result:
        return "UNKNOWN"
    return "YES" if country_name.lower() in result.lower() or result.lower() in country_name.lower() else "NO"

def handle_current_club(db: Session, player_id: str, club_name: str) -> str:
    """Check if the player currently plays for the given club."""
    query = text("""
        SELECT c.name
        FROM players p
        JOIN clubs c ON p.current_club_id = c.id
        WHERE p.id = :pid
    """)
    result = db.execute(query, {"pid": player_id}).scalar()
    if not result:
        return "UNKNOWN"
    return "YES" if club_name.lower() in result.lower() or result.lower() in club_name.lower() else "NO"

def handle_club_history(db: Session, player_id: str, club_name: str) -> str:
    """Check if the player has ever played for the given club."""
    query = text("""
        SELECT COUNT(*)
        FROM player_club_history pch
        JOIN clubs c ON pch.club_id = c.id
        WHERE pch.player_id = :pid AND LOWER(c.name) LIKE :club
    """)
    result = db.execute(query, {"pid": player_id, "club": f"%{club_name.lower()}%"}).scalar()
    return "YES" if result > 0 else "NO"

def handle_position(db: Session, player_id: str, position_group: str) -> str:
    """Check if the player plays in a specific position group."""
    query = text("""
        SELECT position_group
        FROM players
        WHERE id = :pid
    """)
    result = db.execute(query, {"pid": player_id}).scalar()
    if not result:
        return "UNKNOWN"
    return "YES" if result.lower() == position_group.lower() else "NO"

def handle_competition_history(db: Session, player_id: str, competition_name: str) -> str:
    """Check if the player has ever played in the given competition."""
    query = text("""
        SELECT COUNT(*)
        FROM appearances a
        JOIN competitions c ON a.competition_id = c.id
        WHERE a.player_id = :pid AND LOWER(c.name) LIKE :comp
    """)
    result = db.execute(query, {"pid": player_id, "comp": f"%{competition_name.lower()}%"}).scalar()
    return "YES" if result > 0 else "NO"

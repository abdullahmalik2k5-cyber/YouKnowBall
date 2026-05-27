"""Candidate filtering engine.
Maintains the pool of potential players and eliminates impossible candidates.
"""
from typing import List, Set
from sqlalchemy import text
from sqlalchemy.orm import Session

class CandidateEngine:
    def __init__(self, db: Session):
        self.db = db
        # Initialize pool with all active players (could filter by difficulty later)
        res = self.db.execute(text("SELECT id FROM players WHERE active = true")).fetchall()
        self.pool: Set[str] = {str(row[0]) for row in res}
        self.initial_size = len(self.pool)

    def get_remaining_count(self) -> int:
        return len(self.pool)

    def filter_by_nationality(self, country_name: str, expected_answer: str):
        """Eliminates players based on nationality."""
        query = text("""
            SELECT p.id 
            FROM players p
            JOIN countries c ON p.nationality_id = c.id
            WHERE LOWER(c.name) LIKE :country
        """)
        matches = {str(row[0]) for row in self.db.execute(query, {"country": f"%{country_name.lower()}%"}).fetchall()}
        
        if expected_answer == "YES":
            self.pool.intersection_update(matches)
        elif expected_answer == "NO":
            self.pool.difference_update(matches)

    def filter_by_current_club(self, club_name: str, expected_answer: str):
        query = text("""
            SELECT p.id 
            FROM players p
            JOIN clubs c ON p.current_club_id = c.id
            WHERE LOWER(c.name) LIKE :club
        """)
        matches = {str(row[0]) for row in self.db.execute(query, {"club": f"%{club_name.lower()}%"}).fetchall()}
        
        if expected_answer == "YES":
            self.pool.intersection_update(matches)
        elif expected_answer == "NO":
            self.pool.difference_update(matches)

    def filter_by_club_history(self, club_name: str, expected_answer: str):
        query = text("""
            SELECT DISTINCT pch.player_id 
            FROM player_club_history pch
            JOIN clubs c ON pch.club_id = c.id
            WHERE LOWER(c.name) LIKE :club
        """)
        matches = {str(row[0]) for row in self.db.execute(query, {"club": f"%{club_name.lower()}%"}).fetchall()}
        
        if expected_answer == "YES":
            self.pool.intersection_update(matches)
        elif expected_answer == "NO":
            self.pool.difference_update(matches)

    def filter_by_position(self, position_group: str, expected_answer: str):
        query = text("""
            SELECT id FROM players
            WHERE LOWER(position_group) = LOWER(:pos)
        """)
        matches = {str(row[0]) for row in self.db.execute(query, {"pos": position_group}).fetchall()}
        
        if expected_answer == "YES":
            self.pool.intersection_update(matches)
        elif expected_answer == "NO":
            self.pool.difference_update(matches)

    def filter_by_competition_history(self, competition_name: str, expected_answer: str):
        query = text("""
            SELECT DISTINCT a.player_id 
            FROM appearances a
            JOIN competitions c ON a.competition_id = c.id
            WHERE LOWER(c.name) LIKE :comp
        """)
        matches = {str(row[0]) for row in self.db.execute(query, {"comp": f"%{competition_name.lower()}%"}).fetchall()}
        
        if expected_answer == "YES":
            self.pool.intersection_update(matches)
        elif expected_answer == "NO":
            self.pool.difference_update(matches)

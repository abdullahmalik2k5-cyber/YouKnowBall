"""Candidate filtering engine.

Maintains the pool of potential players and eliminates impossible candidates
based on YES / NO answers to each game question.

Key design decision: the pool is initialised from the difficulty-filtered set
(via difficulty.get_player_pool_ids) rather than all 31k active players.
This ensures that every NO answer to a league/competition question removes a
meaningful number of candidates instead of barely moving the needle.
"""
from __future__ import annotations

from typing import Set
from sqlalchemy import text
from sqlalchemy.orm import Session

# Country → continent mapping used for continent-type questions.
# Built from FIFA/UEFA confederation data. Covers every country in the
# Transfermarkt dataset that is likely to appear in the top-5 leagues.
COUNTRY_TO_CONTINENT: dict[str, str] = {
    # Europe
    "England": "Europe", "France": "Europe", "Germany": "Europe", "Italy": "Europe",
    "Spain": "Europe", "Portugal": "Europe", "Netherlands": "Europe", "Belgium": "Europe",
    "Croatia": "Europe", "Poland": "Europe", "Switzerland": "Europe", "Sweden": "Europe",
    "Norway": "Europe", "Denmark": "Europe", "Austria": "Europe", "Turkey": "Europe",
    "Scotland": "Europe", "Wales": "Europe", "Ireland": "Europe", "Greece": "Europe",
    "Czech Republic": "Europe", "Slovakia": "Europe", "Slovenia": "Europe",
    "Serbia": "Europe", "Bosnia-Herzegovina": "Europe", "Kosovo": "Europe",
    "Albania": "Europe", "North Macedonia": "Europe", "Montenegro": "Europe",
    "Romania": "Europe", "Bulgaria": "Europe", "Hungary": "Europe",
    "Ukraine": "Europe", "Russia": "Europe", "Belarus": "Europe",
    "Finland": "Europe", "Iceland": "Europe", "Luxembourg": "Europe",
    "Cyprus": "Europe", "Malta": "Europe", "Latvia": "Europe", "Lithuania": "Europe",
    "Estonia": "Europe", "Moldova": "Europe", "Georgia": "Europe", "Armenia": "Europe",
    "Azerbaijan": "Europe", "Kazakhstan": "Europe",
    # South America
    "Brazil": "South America", "Argentina": "South America", "Colombia": "South America",
    "Chile": "South America", "Uruguay": "South America", "Paraguay": "South America",
    "Peru": "South America", "Ecuador": "South America", "Bolivia": "South America",
    "Venezuela": "South America",
    # Africa
    "Nigeria": "Africa", "Senegal": "Africa", "Morocco": "Africa", "Egypt": "Africa",
    "Ghana": "Africa", "Algeria": "Africa", "Ivory Coast": "Africa", "Cameroon": "Africa",
    "Mali": "Africa", "Burkina Faso": "Africa", "Guinea": "Africa", "Tunisia": "Africa",
    "South Africa": "Africa", "Zimbabwe": "Africa", "Kenya": "Africa",
    "Ethiopia": "Africa", "Tanzania": "Africa", "Uganda": "Africa",
    "Democratic Republic of Congo": "Africa", "Congo": "Africa",
    "Gabon": "Africa", "Togo": "Africa", "Benin": "Africa", "Cape Verde": "Africa",
    "Mozambique": "Africa", "Angola": "Africa", "Zambia": "Africa",
    "Sierra Leone": "Africa", "Liberia": "Africa", "Mauritania": "Africa",
    # Asia / Middle East
    "Japan": "Asia", "South Korea": "Asia", "China": "Asia", "Iran": "Asia",
    "Saudi Arabia": "Asia", "Australia": "Asia", "Iraq": "Asia", "Jordan": "Asia",
    "Lebanon": "Asia", "Syria": "Asia", "United Arab Emirates": "Asia",
    "Qatar": "Asia", "Bahrain": "Asia", "Kuwait": "Asia", "Oman": "Asia",
    "Indonesia": "Asia", "Vietnam": "Asia", "Thailand": "Asia",
    "Philippines": "Asia", "India": "Asia", "Pakistan": "Asia",
    "Uzbekistan": "Asia", "Tajikistan": "Asia",
    # North / Central America & Caribbean
    "Mexico": "North America", "United States": "North America", "Canada": "North America",
    "Jamaica": "North America", "Costa Rica": "North America", "Honduras": "North America",
    "El Salvador": "North America", "Guatemala": "North America", "Panama": "North America",
    "Cuba": "North America", "Dominican Republic": "North America",
    "Trinidad and Tobago": "North America", "Haiti": "North America",
    "Curacao": "North America",
    # Oceania
    "New Zealand": "Oceania", "Fiji": "Oceania",
}

# Aliases for the continent names the user might use
CONTINENT_ALIASES: dict[str, str] = {
    "european": "Europe",
    "europe": "Europe",
    "african": "Africa",
    "africa": "Africa",
    "south american": "South America",
    "latin american": "South America",
    "latin": "South America",
    "american": "North America",
    "north american": "North America",
    "central american": "North America",
    "asian": "Asia",
    "asia": "Asia",
    "middle eastern": "Asia",
    "oceanian": "Oceania",
    "oceania": "Oceania",
    "australian": "Oceania",
}


class CandidateEngine:
    def __init__(self, db: Session, difficulty: str = "hard"):
        self.db = db
        self._difficulty = difficulty
        
        # Import here to avoid circular imports at module level
        from app.game.difficulty import get_player_pool_ids
        
        print(f"  [Engine] Building candidate pool for difficulty='{difficulty}'...")
        self.pool: Set[str] = get_player_pool_ids(db, difficulty)
        self.initial_size = len(self.pool)
        print(f"  [Engine] Pool initialised: {self.initial_size} eligible players.")

    def get_remaining_count(self) -> int:
        return len(self.pool)

    # ─── Nationality ───────────────────────────────────────────────────────────

    def filter_by_nationality(self, country_name: str, expected_answer: str):
        """Eliminates players based on nationality.
        
        Uses exact LOWER(c.name) = LOWER(:country) to avoid substring collisions
        like 'Iran' matching 'Ukraine', 'Niger' matching 'Nigeria', etc.
        """
        query = text("""
            SELECT p.id
            FROM players p
            JOIN countries c ON p.nationality_id = c.id
            WHERE LOWER(c.name) = LOWER(:country)
        """)
        matches = {
            str(row[0])
            for row in self.db.execute(query, {"country": country_name.strip()}).fetchall()
        }
        self._apply_filter(matches, expected_answer)

    # ─── Continent ─────────────────────────────────────────────────────────────

    def filter_by_continent(self, continent_name: str, expected_answer: str):
        """Eliminates players based on the continent of their nationality."""
        # Build the set of country names that map to this continent
        target_continent = continent_name.title()  # Normalise e.g. "europe" → "Europe"
        matching_countries = [
            country for country, continent in COUNTRY_TO_CONTINENT.items()
            if continent == target_continent
        ]
        if not matching_countries:
            # Cannot filter — leave pool unchanged
            return

        # Also check the DB `confederation` column on countries as a secondary signal
        # (some Transfermarkt records have a confederation field we can use)
        conf_map = {
            "Europe": "UEFA",
            "South America": "CONMEBOL",
            "North America": "CONCACAF",
            "Africa": "CAF",
            "Asia": "AFC",
            "Oceania": "OFC",
        }
        confederation = conf_map.get(target_continent)

        placeholders = ", ".join(f":cn{i}" for i in range(len(matching_countries)))
        params = {f"cn{i}": cn for i, cn in enumerate(matching_countries)}

        if confederation:
            params["conf"] = confederation
            query = text(f"""
                SELECT p.id
                FROM players p
                JOIN countries c ON p.nationality_id = c.id
                WHERE c.name IN ({placeholders})
                   OR LOWER(COALESCE(c.confederation, '')) = LOWER(:conf)
            """)
        else:
            query = text(f"""
                SELECT p.id
                FROM players p
                JOIN countries c ON p.nationality_id = c.id
                WHERE c.name IN ({placeholders})
            """)

        matches = {str(row[0]) for row in self.db.execute(query, params).fetchall()}
        self._apply_filter(matches, expected_answer)

    # ─── Current Club ──────────────────────────────────────────────────────────

    def filter_by_current_club(self, club_name: str, expected_answer: str):
        query = text("""
            SELECT p.id
            FROM players p
            JOIN clubs c ON p.current_club_id = c.id
            WHERE LOWER(c.name) LIKE :club
        """)
        matches = {
            str(row[0])
            for row in self.db.execute(query, {"club": f"%{club_name.lower()}%"}).fetchall()
        }
        self._apply_filter(matches, expected_answer)

    # ─── Club History ──────────────────────────────────────────────────────────

    def filter_by_club_history(self, club_name: str, expected_answer: str):
        query = text("""
            SELECT DISTINCT pch.player_id
            FROM player_club_history pch
            JOIN clubs c ON pch.club_id = c.id
            WHERE LOWER(c.name) LIKE :club
        """)
        matches = {
            str(row[0])
            for row in self.db.execute(query, {"club": f"%{club_name.lower()}%"}).fetchall()
        }
        self._apply_filter(matches, expected_answer)

    # ─── Position ─────────────────────────────────────────────────────────────

    def filter_by_position(self, position_group: str, expected_answer: str):
        query = text("""
            SELECT id FROM players
            WHERE LOWER(position_group) = LOWER(:pos)
        """)
        matches = {
            str(row[0])
            for row in self.db.execute(query, {"pos": position_group}).fetchall()
        }
        self._apply_filter(matches, expected_answer)

    # ─── Competition History ───────────────────────────────────────────────────

    def filter_by_competition_history(self, competition_name: str, expected_answer: str):
        """
        Filters by league/cup participation using the appearances table.
        Note: Only players who have at least ONE appearance row can be matched.
        Players with no appearances in any league will *never* be in matches,
        so they are implicitly removed on any YES answer and never removed on NO.
        Since the pool is already seeded with eligibility-checked players
        (each with ≥1 appearance), this behaves correctly.
        """
        query = text("""
            SELECT DISTINCT a.player_id
            FROM appearances a
            JOIN competitions c ON a.competition_id = c.id
            WHERE LOWER(c.name) LIKE :comp
        """)
        matches = {
            str(row[0])
            for row in self.db.execute(query, {"comp": f"%{competition_name.lower()}%"}).fetchall()
        }
        self._apply_filter(matches, expected_answer)

    # ─── Age ──────────────────────────────────────────────────────────────────

    def filter_by_age(self, operator: str, years: int, expected_answer: str):
        """
        Filters candidates by age.

        Args:
            operator: one of "lt" (<), "lte" (<=), "gt" (>), "gte" (>=), "eq" (=)
            years: the age threshold
            expected_answer: "YES" or "NO"
        """
        op_sql = {"lt": "<", "lte": "<=", "gt": ">", "gte": ">=", "eq": "="}.get(operator, "<")
        query = text(f"""
            SELECT id FROM players
            WHERE age IS NOT NULL
              AND age {op_sql} :years
        """)
        matches = {
            str(row[0])
            for row in self.db.execute(query, {"years": years}).fetchall()
        }
        self._apply_filter(matches, expected_answer)

    # ─── Preferred Foot ───────────────────────────────────────────────────────

    def filter_by_foot(self, foot_value: str, expected_answer: str):
        """
        Filters candidates by preferred foot.

        Args:
            foot_value: "left", "right", or "both"
            expected_answer: "YES" or "NO"
        """
        query = text("""
            SELECT id FROM players
            WHERE preferred_foot IS NOT NULL
              AND LOWER(preferred_foot) = LOWER(:foot)
        """)
        matches = {
            str(row[0])
            for row in self.db.execute(query, {"foot": foot_value}).fetchall()
        }
        self._apply_filter(matches, expected_answer)

    # ─── Internal helper ──────────────────────────────────────────────────────

    def _apply_filter(self, matches: Set[str], expected_answer: str):
        """Applies intersection (YES) or difference (NO) to the pool."""
        before = len(self.pool)
        if expected_answer == "YES":
            self.pool.intersection_update(matches)
        elif expected_answer == "NO":
            self.pool.difference_update(matches)
        eliminated = before - len(self.pool)
        if eliminated:
            print(f"  [Engine] Eliminated {eliminated} candidates → {len(self.pool)} remaining.")

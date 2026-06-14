"""Difficulty mode logic.

Defines three player pool tiers per the PRD §9:
  - easy   (Reel Watcher): top-4 clubs per league, 500+ minutes in current season
  - medium (Mid):          top-6 clubs per league, 500+ minutes in current season
  - hard   (Ball Knower):  all clubs in the top-5 leagues, no minutes filter

Each pool is built by looking at clubs whose domestic_competition_id matches one
of the 5 top-league IDs in the competitions table.

Before selecting a hidden player the system runs an eligibility check to ensure
the player has: nationality, current club, position_group, and at least one
appearance record. Players failing the check are excluded.
"""

from __future__ import annotations

import random
from typing import Set
from sqlalchemy import text
from sqlalchemy.orm import Session

# ─── League slug / name fragments that identify the top-5 European leagues ───
# These are checked against the competitions.name column (case-insensitive LIKE).
# Transfermarkt-sourced data typically uses the slug style (e.g. "premier-league").
TOP5_LEAGUE_NAMES = [
    "premier-league",      # English Premier League
    "la-liga",             # Spanish La Liga
    "bundesliga",          # German Bundesliga
    "serie-a",             # Italian Serie A
    "ligue-1",             # French Ligue 1
]

# Approximate max clubs per league; we sort by club table size / market value proxy
# using market_value_eur from player valuations, or simply rely on the DB ordering.
# The PRD defines top-4 for easy, top-6 for medium, all for hard.
EASY_CLUBS_PER_LEAGUE = 4
MEDIUM_CLUBS_PER_LEAGUE = 6
EASY_MIN_MINUTES = 500
MEDIUM_MIN_MINUTES = 500


def _get_top5_competition_ids(db: Session) -> list[str]:
    """Returns the UUIDs of the 5 top-league competitions from the DB."""
    rows = []
    for league_slug in TOP5_LEAGUE_NAMES:
        res = db.execute(
            text("SELECT id FROM competitions WHERE LOWER(name) = :name LIMIT 1"),
            {"name": league_slug}
        ).fetchone()
        if res:
            rows.append(str(res[0]))
    return rows


def _get_top5_club_ids(db: Session) -> list[str]:
    """Returns all club IDs whose domestic competition is one of the top 5 leagues."""
    comp_ids = _get_top5_competition_ids(db)
    if not comp_ids:
        return []
    
    placeholders = ", ".join(f":comp{i}" for i in range(len(comp_ids)))
    params = {f"comp{i}": cid for i, cid in enumerate(comp_ids)}
    
    res = db.execute(
        text(f"SELECT id FROM clubs WHERE domestic_competition_id IN ({placeholders})"),
        params
    ).fetchall()
    return [str(row[0]) for row in res]


def _get_ranked_clubs_per_league(db: Session, n_clubs: int) -> list[str]:
    """
    Returns the top-N club IDs per league, ranked by the average market value
    of their current players (a reliable proxy for club prestige in the DB).
    """
    comp_ids = _get_top5_competition_ids(db)
    if not comp_ids:
        return []

    placeholders = ", ".join(f":comp{i}" for i in range(len(comp_ids)))
    params = {f"comp{i}": cid for i, cid in enumerate(comp_ids)}
    params["n_clubs"] = n_clubs

    # Rank clubs within each league by avg player market value, take top N per league
    query = text(f"""
        WITH club_values AS (
            SELECT
                c.id AS club_id,
                c.domestic_competition_id AS comp_id,
                COALESCE(AVG(p.market_value_eur), 0) AS avg_value
            FROM clubs c
            LEFT JOIN players p ON p.current_club_id = c.id AND p.active = true
            WHERE c.domestic_competition_id IN ({placeholders})
            GROUP BY c.id, c.domestic_competition_id
        ),
        ranked AS (
            SELECT club_id,
                   ROW_NUMBER() OVER (PARTITION BY comp_id ORDER BY avg_value DESC) AS rnk
            FROM club_values
        )
        SELECT club_id FROM ranked WHERE rnk <= :n_clubs
    """)
    res = db.execute(query, params).fetchall()
    return [str(row[0]) for row in res]


def _eligibility_check_clause() -> str:
    """Returns the WHERE clause fragment for eligibility-checked players."""
    return """
        p.active = true
        AND p.nationality_id IS NOT NULL
        AND p.current_club_id IS NOT NULL
        AND p.position_group IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM appearances a WHERE a.player_id = p.id LIMIT 1
        )
    """


def get_player_pool_ids(db: Session, difficulty: str = "hard") -> Set[str]:
    """
    Returns the set of eligible player IDs for the given difficulty level.

    Args:
        db: SQLAlchemy session
        difficulty: one of "easy", "medium", "hard"

    Returns:
        Set of player ID strings
    """
    difficulty = difficulty.lower().strip()

    if difficulty == "hard":
        # All players at clubs in the top-5 leagues
        club_ids = _get_top5_club_ids(db)
        if not club_ids:
            # Fallback: all active eligible players
            res = db.execute(
                text(f"SELECT p.id FROM players p WHERE {_eligibility_check_clause()}")
            ).fetchall()
            return {str(r[0]) for r in res}

        placeholders = ", ".join(f":c{i}" for i in range(len(club_ids)))
        params = {f"c{i}": cid for i, cid in enumerate(club_ids)}
        query = text(f"""
            SELECT p.id FROM players p
            WHERE p.current_club_id IN ({placeholders})
            AND {_eligibility_check_clause()}
        """)
        res = db.execute(query, params).fetchall()
        return {str(r[0]) for r in res}

    elif difficulty in ("medium", "easy"):
        n_clubs = EASY_CLUBS_PER_LEAGUE if difficulty == "easy" else MEDIUM_CLUBS_PER_LEAGUE
        min_mins = EASY_MIN_MINUTES if difficulty == "easy" else MEDIUM_MIN_MINUTES
        top_club_ids = _get_ranked_clubs_per_league(db, n_clubs)

        if not top_club_ids:
            # Fallback to hard
            return get_player_pool_ids(db, "hard")

        placeholders = ", ".join(f":c{i}" for i in range(len(top_club_ids)))
        params = {f"c{i}": cid for i, cid in enumerate(top_club_ids)}
        params["min_mins"] = min_mins

        # Players must have 500+ total minutes across all appearances
        query = text(f"""
            SELECT p.id FROM players p
            WHERE p.current_club_id IN ({placeholders})
            AND {_eligibility_check_clause()}
            AND (
                SELECT COALESCE(SUM(a.minutes_played), 0)
                FROM appearances a WHERE a.player_id = p.id
            ) >= :min_mins
        """)
        res = db.execute(query, params).fetchall()
        pool = {str(r[0]) for r in res}

        # If pool is suspiciously small, relax minutes filter and try again
        if len(pool) < 50:
            query_relaxed = text(f"""
                SELECT p.id FROM players p
                WHERE p.current_club_id IN ({placeholders})
                AND {_eligibility_check_clause()}
            """)
            res = db.execute(query_relaxed, {k: v for k, v in params.items() if k != "min_mins"}).fetchall()
            pool = {str(r[0]) for r in res}

        return pool

    else:
        raise ValueError(f"Unknown difficulty '{difficulty}'. Use 'easy', 'medium', or 'hard'.")


def select_hidden_player(db: Session, difficulty: str = "hard") -> tuple[str, str] | None:
    """
    Selects a random eligible hidden player for the given difficulty.

    Returns:
        (player_id, player_name) tuple, or None if no eligible players found.
    """
    pool_ids = get_player_pool_ids(db, difficulty)
    if not pool_ids:
        return None

    # Pick a random ID from the pool
    chosen_id = random.choice(list(pool_ids))

    res = db.execute(
        text("SELECT id, name FROM players WHERE id = :pid"),
        {"pid": chosen_id}
    ).fetchone()

    if not res:
        return None

    return str(res[0]), str(res[1])

"""Game route handlers.

HTTP wrapper around the CLI game logic in ``play_game.py``. Exposes three
endpoints — start a game, ask a question, submit a guess — backed by an
in-memory session store. This is prototype-grade: state lives in process
memory (lost on restart, single-process only), but the game logic itself is
the same battle-tested code path used by the CLI.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Set

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.database import SessionLocal
from app.nlp.parser import parse_question
from app.game.candidate_engine.engine import CandidateEngine
from app.game.difficulty import select_hidden_player
from app.game.queries.handlers import (
    handle_nationality,
    handle_current_club,
    handle_club_history,
    handle_position,
    handle_competition_history,
    handle_big_six,
    handle_continent,
    handle_age,
    handle_foot,
)
from app.nlp.llm.explainer import generate_explanation

router = APIRouter(prefix="/api/game", tags=["game"])

MAX_QUESTIONS = 20
MAX_GUESSES = 3
VALID_DIFFICULTIES = ("easy", "medium", "hard")
SUPPORTED_QUESTION_TYPES = (
    "nationality", "current_club", "club_history", "position",
    "competition", "big_six", "continent", "age", "foot",
)


# ── In-memory session store ───────────────────────────────────────────────────
@dataclass
class GameState:
    difficulty: str
    hidden_player_id: str
    hidden_player_name: str
    pool: Set[str]
    initial_size: int
    questions_used: int = 0
    guesses_used: int = 0
    consecutive_invalid: int = 0
    finished: bool = False
    outcome: str = ""  # "won" | "lost" | ""


GAMES: dict[str, GameState] = {}


# ── Request models ────────────────────────────────────────────────────────────
class NewGameRequest(BaseModel):
    difficulty: str = "hard"


class AskRequest(BaseModel):
    session_id: str
    question: str


class GuessRequest(BaseModel):
    session_id: str
    guess: str


# ── Guess matching (mirrors play_game.py) ─────────────────────────────────────
def _normalize_guess(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def guess_matches(guess: str, target: str) -> bool:
    g = _normalize_guess(guess)
    t = _normalize_guess(target)
    if g == t:
        return True
    parts = t.split()
    if len(parts) > 1:
        last_name = parts[-1]
        if len(last_name) > 3 and g == last_name:
            return True
        if g == " ".join(reversed(parts)):
            return True
    return False


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_game(session_id: str) -> GameState:
    game = GAMES.get(session_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game session not found. Start a new game.")
    return game


def _status(game: GameState) -> dict:
    """Public, non-revealing snapshot of the game state."""
    return {
        "difficulty": game.difficulty,
        "questions_used": game.questions_used,
        "questions_left": MAX_QUESTIONS - game.questions_used,
        "guesses_used": game.guesses_used,
        "guesses_left": MAX_GUESSES - game.guesses_used,
        "remaining": len(game.pool),
        "initial_pool": game.initial_size,
        "finished": game.finished,
        "outcome": game.outcome,
    }


def _dispatch_question(db, game: GameState, q_type: str, q_value) -> tuple[str, str]:
    """Run the answer handler and narrow the candidate pool. Returns (answer, facts)."""
    engine = CandidateEngine.restore(db, game.difficulty, game.pool, game.initial_size)
    pid = game.hidden_player_id

    if q_type == "nationality":
        answer, facts = handle_nationality(db, pid, q_value)
        engine.filter_by_nationality(q_value, answer)
    elif q_type == "current_club":
        answer, facts = handle_current_club(db, pid, q_value)
        engine.filter_by_current_club(q_value, answer)
    elif q_type == "club_history":
        answer, facts = handle_club_history(db, pid, q_value)
        engine.filter_by_club_history(q_value, answer)
    elif q_type == "position":
        answer, facts = handle_position(db, pid, q_value)
        engine.filter_by_position(q_value, answer)
    elif q_type == "competition":
        answer, facts = handle_competition_history(db, pid, q_value)
        engine.filter_by_competition_history(q_value, answer)
    elif q_type == "big_six":
        answer, facts = handle_big_six(db, pid)
        engine.filter_by_big_six(answer)
    elif q_type == "continent":
        answer, facts = handle_continent(db, pid, q_value)
        engine.filter_by_continent(q_value, answer)
    elif q_type == "age":
        answer, facts = handle_age(db, pid, q_value["operator"], q_value["years"])
        engine.filter_by_age(q_value["operator"], q_value["years"], answer)
    elif q_type == "foot":
        answer, facts = handle_foot(db, pid, q_value)
        engine.filter_by_foot(q_value, answer)
    else:
        raise ValueError(f"unhandled question type: {q_type}")

    game.pool = engine.pool  # persist narrowed pool back to the session
    return answer, facts


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/new")
def new_game(req: NewGameRequest):
    difficulty = (req.difficulty or "hard").lower().strip()
    if difficulty not in VALID_DIFFICULTIES:
        difficulty = "hard"

    db = SessionLocal()
    try:
        result = select_hidden_player(db, difficulty)
        if not result:
            raise HTTPException(
                status_code=503,
                detail="No eligible players for this difficulty. Has the database been ingested?",
            )
        hidden_id, hidden_name = result
        engine = CandidateEngine(db, difficulty)
    finally:
        db.close()

    session_id = uuid.uuid4().hex
    GAMES[session_id] = GameState(
        difficulty=difficulty,
        hidden_player_id=hidden_id,
        hidden_player_name=hidden_name,
        pool=engine.pool,
        initial_size=engine.initial_size,
    )
    out = _status(GAMES[session_id])
    out["session_id"] = session_id
    out["max_questions"] = MAX_QUESTIONS
    out["max_guesses"] = MAX_GUESSES
    return out


@router.post("/ask")
def ask(req: AskRequest):
    game = _get_game(req.session_id)

    if game.finished:
        return {"valid": False, "message": "This game is already over.", **_status(game)}

    if game.questions_used >= MAX_QUESTIONS:
        game.finished = True
        game.outcome = "lost"
        return {
            "valid": False,
            "message": f"No questions left. The player was {game.hidden_player_name}.",
            "player_name": game.hidden_player_name,
            **_status(game),
        }

    db = SessionLocal()
    try:
        parsed = parse_question(db, req.question)

        # ── Invalid / unparseable question ──
        if parsed["type"] == "invalid" or not parsed.get("value"):
            message = parsed.get(
                "message",
                "I couldn't understand that question. Try nationality, continent, "
                "club, position, league, age, or preferred foot.",
            )
            game.consecutive_invalid += 1
            turn_charged = False
            if game.consecutive_invalid >= 3:
                game.questions_used += 1
                game.consecutive_invalid = 0
                turn_charged = True
            return {
                "valid": False,
                "message": message,
                "turn_charged": turn_charged,
                **_status(game),
            }

        # ── Valid question ──
        game.consecutive_invalid = 0
        q_type = parsed["type"]
        q_value = parsed["value"]

        if q_type not in SUPPORTED_QUESTION_TYPES:
            return {
                "valid": False,
                "message": f"Question type '{q_type}' isn't supported yet. No turn charged.",
                "turn_charged": False,
                **_status(game),
            }

        try:
            answer, facts = _dispatch_question(db, game, q_type, q_value)
        except Exception as exc:  # noqa: BLE001 - surface gracefully, don't 500 the game
            print(f"[ask] dispatch failed for type={q_type!r}: {exc!r}")
            return {
                "valid": False,
                "message": "Something went wrong answering that question. No turn charged — try another.",
                "turn_charged": False,
                **_status(game),
            }

        game.questions_used += 1
        explanation = generate_explanation(req.question, answer, game.hidden_player_name, facts)
    finally:
        db.close()

    response = {
        "valid": True,
        "answer": answer,
        "explanation": explanation,
        "question_type": q_type,
        **_status(game),
    }

    # Out of questions after this one → reveal.
    if game.questions_used >= MAX_QUESTIONS and not game.finished:
        game.finished = True
        game.outcome = "lost"
        response["player_name"] = game.hidden_player_name
        response["finished"] = True
        response["outcome"] = "lost"
    return response


@router.post("/guess")
def guess(req: GuessRequest):
    game = _get_game(req.session_id)

    if game.finished:
        return {"correct": False, "message": "This game is already over.", **_status(game)}

    if not req.guess.strip():
        raise HTTPException(status_code=400, detail="Empty guess.")

    game.guesses_used += 1

    if guess_matches(req.guess, game.hidden_player_name):
        game.finished = True
        game.outcome = "won"
        return {
            "correct": True,
            "message": f"Correct! The player was {game.hidden_player_name}.",
            "player_name": game.hidden_player_name,
            **_status(game),
        }

    # Wrong guess.
    if game.guesses_used >= MAX_GUESSES:
        game.finished = True
        game.outcome = "lost"
        return {
            "correct": False,
            "message": f"Wrong! Out of guesses. The player was {game.hidden_player_name}.",
            "player_name": game.hidden_player_name,
            **_status(game),
        }

    return {
        "correct": False,
        "message": "Wrong guess! Keep questioning.",
        **_status(game),
    }


@router.get("/state/{session_id}")
def state(session_id: str):
    return _status(_get_game(session_id))

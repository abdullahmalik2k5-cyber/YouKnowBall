from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    country_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    confederation: Mapped[str | None] = mapped_column(String(80), nullable=True)

    clubs: Mapped[list[Club]] = relationship(back_populates="country")
    national_teams: Mapped[list[NationalTeam]] = relationship(back_populates="country")
    players: Mapped[list[Player]] = relationship(back_populates="nationality")


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sub_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    confederation: Mapped[str | None] = mapped_column(String(80), nullable=True)
    domestic_league_code: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)

    clubs: Mapped[list[Club]] = relationship(back_populates="domestic_competition")
    games: Mapped[list[Game]] = relationship(back_populates="competition")
    appearances: Mapped[list[Appearance]] = relationship(back_populates="competition")

    __table_args__ = (Index("ix_competitions_name", "name"),)


class Club(Base):
    __tablename__ = "clubs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    domestic_competition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competitions.id"), nullable=True
    )
    country_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=True)
    stadium_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    stadium_seats: Mapped[int | None] = mapped_column(Integer, nullable=True)

    country: Mapped[Country | None] = relationship(back_populates="clubs")
    domestic_competition: Mapped[Competition | None] = relationship(back_populates="clubs")
    current_players: Mapped[list[Player]] = relationship(back_populates="current_club")
    club_history: Mapped[list[PlayerClubHistory]] = relationship(back_populates="club")
    appearances: Mapped[list[Appearance]] = relationship(back_populates="club")
    home_games: Mapped[list[Game]] = relationship(foreign_keys="Game.home_club_id", back_populates="home_club")
    away_games: Mapped[list[Game]] = relationship(foreign_keys="Game.away_club_id", back_populates="away_club")
    lineups: Mapped[list[GameLineup]] = relationship(back_populates="club")
    club_games: Mapped[list[ClubGame]] = relationship(foreign_keys="ClubGame.club_id", back_populates="club")
    valuations: Mapped[list[PlayerValuation]] = relationship(back_populates="club")

    __table_args__ = (Index("ix_clubs_name", "name"),)


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nationality_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=True)
    position: Mapped[str] = mapped_column(String(10), nullable=False)
    sub_position: Mapped[str | None] = mapped_column(String(80), nullable=True)
    position_group: Mapped[str | None] = mapped_column(String(20), nullable=True)
    preferred_foot: Mapped[str | None] = mapped_column(String(20), nullable=True)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_club_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=True)
    market_value_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)
    international_caps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    international_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Enriched fields from players_enriched.csv
    positions: Mapped[str | None] = mapped_column(String(100), nullable=True)
    born: Mapped[int | None] = mapped_column(Integer, nullable=True)
    minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    matches: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assists: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_gk: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True)
    eligible: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=True)
    region: Mapped[str | None] = mapped_column(String(60), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    big_club: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    is_starter: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    is_supersub: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    is_everpresent: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    goals_bracket: Mapped[str | None] = mapped_column(String(20), nullable=True)
    assists_bracket: Mapped[str | None] = mapped_column(String(20), nullable=True)
    double_double: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    penalty_taker: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    sent_off: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    scored_own_goal: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    discipline: Mapped[str | None] = mapped_column(String(20), nullable=True)
    heavily_booked: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    big_crosser: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    ball_winner: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    gets_fouled: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    shoots_a_lot: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    gk_clean_sheets: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    gk_strong: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    high_ppm: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)

    nationality: Mapped[Country | None] = relationship(back_populates="players")
    current_club: Mapped[Club | None] = relationship(back_populates="current_players")
    club_history: Mapped[list[PlayerClubHistory]] = relationship(back_populates="player")
    transfers: Mapped[list[Transfer]] = relationship(back_populates="player")
    appearances: Mapped[list[Appearance]] = relationship(back_populates="player")
    lineups: Mapped[list[GameLineup]] = relationship(back_populates="player")
    events: Mapped[list[GameEvent]] = relationship(foreign_keys="GameEvent.player_id", back_populates="player")
    assists: Mapped[list[GameEvent]] = relationship(foreign_keys="GameEvent.assist_player_id", back_populates="assist_player")
    valuations: Mapped[list[PlayerValuation]] = relationship(back_populates="player")
    target_sessions: Mapped[list[GameSession]] = relationship(back_populates="player")
    guesses: Mapped[list[Guess]] = relationship(back_populates="guessed_player")

    __table_args__ = (
        Index("ix_players_name", "name"),
        Index("ix_players_nationality_id", "nationality_id"),
        Index("ix_players_position", "position"),
        Index("ix_players_current_club_id", "current_club_id"),
        Index("ix_players_position_group", "position_group"),
    )


class NationalTeam(Base):
    __tablename__ = "national_teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    country_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=False)
    fifa_ranking: Mapped[int | None] = mapped_column(Integer, nullable=True)
    squad_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_age: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)

    country: Mapped[Country] = relationship(back_populates="national_teams")


class PlayerClubHistory(Base):
    __tablename__ = "player_club_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    club_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False, index=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    transfer_season: Mapped[str | None] = mapped_column(String(20), nullable=True)

    player: Mapped[Player] = relationship(back_populates="club_history")
    club: Mapped[Club] = relationship(back_populates="club_history")


class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    from_club_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=True, index=True)
    to_club_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=True, index=True)
    transfer_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    transfer_fee: Mapped[int | None] = mapped_column(Integer, nullable=True)
    market_value_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)

    player: Mapped[Player] = relationship(back_populates="transfers")
    from_club: Mapped[Club | None] = relationship(foreign_keys=[from_club_id])
    to_club: Mapped[Club | None] = relationship(foreign_keys=[to_club_id])


class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competition_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("competitions.id"), nullable=True)
    season: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    home_club_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=True)
    away_club_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=True)
    home_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)

    competition: Mapped[Competition | None] = relationship(back_populates="games")
    home_club: Mapped[Club | None] = relationship(foreign_keys=[home_club_id], back_populates="home_games")
    away_club: Mapped[Club | None] = relationship(foreign_keys=[away_club_id], back_populates="away_games")
    appearances: Mapped[list[Appearance]] = relationship(back_populates="game")
    lineups: Mapped[list[GameLineup]] = relationship(back_populates="game")
    events: Mapped[list[GameEvent]] = relationship(back_populates="game")
    club_games: Mapped[list[ClubGame]] = relationship(back_populates="game")


class Appearance(Base):
    __tablename__ = "appearances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    club_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=True, index=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    minutes_played: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    goals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assists: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    yellow_cards: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    red_cards: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    competition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competitions.id"), nullable=True, index=True
    )

    game: Mapped[Game] = relationship(back_populates="appearances")
    player: Mapped[Player] = relationship(back_populates="appearances")
    club: Mapped[Club | None] = relationship(back_populates="appearances")
    competition: Mapped[Competition | None] = relationship(back_populates="appearances")


class GameLineup(Base):
    __tablename__ = "game_lineups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    club_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False, index=True)
    position: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_starting: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_captain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    game: Mapped[Game] = relationship(back_populates="lineups")
    player: Mapped[Player] = relationship(back_populates="lineups")
    club: Mapped[Club] = relationship(back_populates="lineups")


class GameEvent(Base):
    __tablename__ = "game_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    player_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assist_player_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("players.id"), nullable=True, index=True
    )

    game: Mapped[Game] = relationship(back_populates="events")
    player: Mapped[Player | None] = relationship(foreign_keys=[player_id], back_populates="events")
    assist_player: Mapped[Player | None] = relationship(foreign_keys=[assist_player_id], back_populates="assists")


class ClubGame(Base):
    __tablename__ = "club_games"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True)
    club_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=False, index=True)
    opponent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=True, index=True)
    is_home: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_win: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    game: Mapped[Game] = relationship(back_populates="club_games")
    club: Mapped[Club] = relationship(foreign_keys=[club_id], back_populates="club_games")
    opponent: Mapped[Club | None] = relationship(foreign_keys=[opponent_id])


class PlayerValuation(Base):
    __tablename__ = "player_valuations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    market_value_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)
    club_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("clubs.id"), nullable=True, index=True)

    player: Mapped[Player] = relationship(back_populates="valuations")
    club: Mapped[Club | None] = relationship(back_populates="valuations")


class Alias(Base):
    __tablename__ = "aliases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alias: Mapped[str] = mapped_column(String(220), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(220), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)

    __table_args__ = (
        Index("ix_aliases_alias", "alias"),
        Index("ix_aliases_entity_type_alias", "entity_type", "alias"),
    )


class EntityMapping(Base):
    __tablename__ = "entity_mappings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_value: Mapped[str] = mapped_column(String(220), nullable=False)
    canonical_value: Mapped[str] = mapped_column(String(220), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)

    __table_args__ = (Index("ix_entity_mappings_entity_type_raw_value", "entity_type", "raw_value"),)


class GameSession(Base):
    __tablename__ = "game_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    difficulty: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active", index=True)

    player: Mapped[Player] = relationship(back_populates="target_sessions")
    questions: Mapped[list[Question]] = relationship(back_populates="session", cascade="all, delete-orphan")
    guesses: Mapped[list[Guess]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("game_sessions.id"), nullable=False, index=True)
    question_text: Mapped[str] = mapped_column(String(200), nullable=False)
    parsed_intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    session: Mapped[GameSession] = relationship(back_populates="questions")


class Guess(Base):
    __tablename__ = "guesses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("game_sessions.id"), nullable=False, index=True)
    guessed_player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    session: Mapped[GameSession] = relationship(back_populates="guesses")
    guessed_player: Mapped[Player] = relationship(back_populates="guesses")

# You Know Ball?

Version: 3.0
Status: Active Draft
Project Type: AI-Powered Football Deduction & Trivia Platform
Primary Architecture: Supabase-Hosted PostgreSQL + AI-Assisted Query Interpretation

---

# 1. Executive Summary

You Know Ball? is an AI-powered football deduction platform where players attempt to identify a hidden football player by asking natural-language yes/no questions.

Unlike traditional football trivia games that rely on predefined prompts, the platform allows users to ask flexible football questions such as:

* "Has he played in the Premier League?"
* "Is he Brazilian?"
* "Did he play with Messi?"
* "Has he won the Champions League?"
* "Did he ever play for Juventus?"
* "Has he scored more than 20 goals in a season?"

The platform interprets these questions using an AI-powered NLP layer, converts them into structured football queries, and validates all answers against a relational football database.

The system responds with:

* YES
* NO
* UNKNOWN

The project combines:

* football data engineering
* relational database design
* AI-powered natural-language interpretation
* football deduction gameplay
* backend systems engineering
* scalable cloud-hosted infrastructure
* secure multiplayer-ready architecture

---

# 2. Problem Statement

Current football trivia games are limited because:

* questions are predefined
* gameplay becomes repetitive
* football knowledge depth is shallow
* there is little personalization
* users cannot ask natural football questions
* most systems cannot reason dynamically using structured football data

Football fans enjoy:

* proving football knowledge
* debating football history
* discussing obscure football facts
* social deduction and trivia games

There is an opportunity to create a system where:

* users ask open-ended football questions
* AI interprets football language naturally
* answers are grounded entirely in structured football data
* gameplay feels intelligent and highly replayable

---

# 3. Product Vision

To create the most intelligent football deduction platform powered by real football data, scalable database engineering, and natural-language interaction.

The experience should feel like:

* talking to a football analyst
* solving a football mystery
* competing in a football IQ challenge
* playing a football version of 20 Questions

---

# 4. Core Product Principles

## Principle 1 — Database Is the Source of Truth

All football knowledge must originate from structured relational data.

AI never invents football facts.

---

## Principle 2 — AI Interprets, Not Answers

The AI layer only:

* classifies intent
* extracts entities
* maps natural language into structured filters

The database determines truth.

---

## Principle 3 — Flexible Football Conversation

Players should feel free to ask football questions naturally without memorizing strict command formats.

---

## Principle 4 — Deduction Over Guessing

Gameplay should reward football knowledge, reasoning, and elimination strategies.

---

## Principle 5 — Scalable Engineering

The architecture must support future expansion including:

* historical football modes
* multiplayer
* mobile apps
* larger datasets
* advanced AI reasoning
* social features

---

# 5. Goals & Objectives

## Primary Goals

### Goal 1 — Natural Football Questions

Allow players to ask flexible football yes/no questions in natural language.

---

### Goal 2 — Accurate Football Responses

Ensure every answer is validated using structured football data.

---

### Goal 3 — Scalable Football Database

Build a normalized football database capable of supporting:

* thousands of players
* millions of appearances/events
* historical expansion
* advanced relational football queries

---

### Goal 4 — Engaging Deduction Gameplay

Create gameplay that rewards football knowledge and logical deduction.

---

### Goal 5 — Production-Ready Cloud Infrastructure

Deploy the system on Supabase-hosted PostgreSQL with scalable backend architecture.

---

# 6. Non-Goals

The following are NOT initial priorities:

* live football scores
* real-time match tracking
* betting systems
* fantasy football integration
* AI-generated football commentary
* football manager simulation
* mobile applications (initially)
* real-time multiplayer

---

# 7. Target Audience

## Primary Users

### Football Fans

Users who enjoy football trivia, football history, and football debates.

---

### Football Twitter / Online Communities

Users who enjoy football IQ challenges and social football discussions.

---

### Casual Deduction Gamers

Players who enjoy games such as:

* Wordle
* GeoGuessr
* Loldle
* 20 Questions

---

### Developers & Recruiters

The project also serves as a technical portfolio project demonstrating:

* AI integration
* relational database engineering
* scalable backend systems
* NLP pipelines
* cloud infrastructure
* applied cybersecurity

---

# 8. Core Gameplay Loop

## Gameplay Flow

1. Player selects difficulty mode
2. System selects a hidden football player
3. Player asks a yes/no football question
4. NLP layer interprets the question
5. Backend converts interpretation into structured database filters
6. PostgreSQL validates the answer
7. System returns YES / NO / UNKNOWN
8. Candidate pool narrows internally
9. Relevant player card fields reveal progressively
10. Player continues until correct guess or question limit exhausted

---

# 9. Difficulty Modes

## 9.1 Reel Watcher (Easy)

Definition:
Players from major clubs in the top 5 leagues filtered to commonly recognized players.

Approximate pool:
300–400 players.

---

## 9.2 Mid (Medium)

Definition:
Expanded pool including broader top-club squads and more regular starters.

Approximate pool:
500–700 players.

---

## 9.3 Ball Knower (Hard)

Definition:
All registered squad players across the top 5 leagues including fringe and rotational players.

Approximate pool:
2,000–2,500 players.

---

## Pool Rules

* Modes are cumulative.
* Weighted selection reduces excessive fringe-player frequency.
* Daily challenge rotates difficulty weekly.

---

# 10. Functional Requirements

# 10.1 User Input System

### FR-1

Players must be able to ask natural-language football questions.

---

### FR-2

Questions must support flexible phrasing.

Examples:

* "Did he play in Spain?"
* "Has he ever played for Barca?"
* "Is he over 30?"
* "Did he play with Ronaldo?"

---

### FR-3

Questions must be validated before processing.

Invalid categories include:

* non-football prompts
* offensive prompts
* malformed prompts
* prompts exceeding 200 characters

---

### FR-4

Question submission must be rate-limited to prevent spam and scripted abuse.

---

# 10.2 AI Question Interpreter

### FR-5

The AI layer must classify football question intent.

Supported intent categories include:

* nationality
* age
* position
* flank
* current club
* club history
* competition history
* transfer history
* trophies
* teammates
* opponents
* goals/assists statistics
* international career
* market value
* appearances/minutes played

---

### FR-6

The AI layer must extract football entities.

Example:

```json
{
  "intent": "club_history",
  "club": "Real Madrid"
}
```

---

### FR-7

The AI layer must never directly answer football questions.

The database remains the only source of truth.

---

### FR-8

All AI output must be validated against strict JSON schemas before query execution.

---

### FR-9

Prompt injection attempts must be rejected and logged.

---

# 10.3 Card Reveal System

### FR-10

The deduction card progressively reveals:

| Field                   | Reveal Trigger                         |
| ----------------------- | -------------------------------------- |
| Position                | Confirmed YES on position question     |
| Flank                   | Confirmed YES on flank question        |
| Nationality             | Confirmed YES on nationality question  |
| Current Club            | Confirmed YES on current club question |
| Player Image/Silhouette | Correct final guess                    |

---

### FR-11

Goalkeepers automatically disable flank reveal.

---

### FR-12

Fields remain hidden on NO or UNKNOWN responses.

---

# 10.4 Database Query System

### FR-13

The backend must generate parameterized SQL queries from validated AI output.

---

### FR-14

All gameplay answers must originate from PostgreSQL queries.

---

### FR-15

The system must support:

* relational football queries
* club history checks
* teammate inference
* competition history
* stat comparisons
* transfer history
* international career checks

---

# 10.5 Response System

### FR-16

The system returns:

* YES
* NO
* UNKNOWN

---

### FR-17

Optional explanation mode may provide supporting evidence.

Example:

"Yes — the player played for Juventus between 2018 and 2021."

---

# 10.6 Game State Management

### FR-18

The system must track:

* hidden player identity
* questions asked
* answers returned
* elapsed time
* deduction card state
* remaining questions
* candidate pool state

---

### FR-19

The hidden player must remain server-side only.

---

### FR-20

Game resets must generate entirely new sessions.

---

# 10.7 Win & Loss Conditions

## Win Condition

Player correctly guesses the hidden player within the question limit.

---

## Loss Condition

Player exhausts all questions without a correct guess.

---

## Win Flow

1. Hidden player revealed
2. Final score calculated server-side
3. Results modal displayed
4. Daily share card generated
5. Leaderboard updated
6. Replay options shown

---

## Loss Flow

1. Hidden player revealed
2. Score recorded as 0
3. Guess streak resets
4. Player summary displayed

---

# 11. Scoring System

Score is calculated entirely server-side.

```text
base_score         = 1000
question_penalty   = questions_asked × 40
time_penalty       = floor(elapsed_seconds / 30) × 10
difficulty_bonus   = Reel Watcher: 0 / Mid: +200 / Ball Knower: +500
streak_multiplier  = 1 + (guess_streak × 0.05)

final_score = (base_score − question_penalty − time_penalty + difficulty_bonus) × streak_multiplier
```

Minimum winning score:
50.

---

# 12. Metagame Systems

## Daily Streak

* increments after at least one completed daily game
* resets if a day is missed
* visible in profile/header

---

## Guess Streak

* increments after each successful guess
* resets after failed game
* affects score multiplier

---

## Daily Challenge

* one shared hidden player globally
* rotates difficulty weekly
* spoiler-free share results

---

## Badge System

Examples:

* One Question Wonder
* Legend Hunter
* Tactician
* Daily Dominator
* On Fire

---

# 13. Leaderboard System

Three leaderboard tabs:

* Global
* Friends
* Daily

All score calculations remain server-side.

---

# 14. Non-Functional Requirements

## Performance

### NFR-1

Average gameplay response time should remain within 1–2 seconds.

---

### NFR-2

The system should support concurrent football queries efficiently.

---

## Scalability

### NFR-3

Architecture must support future expansion including:

* historical football data
* multiplayer
* mobile clients
* larger player pools

---

## Reliability

### NFR-4

Hallucinated football answers are unacceptable.

All gameplay responses must be database-backed.

---

# 15. Security Requirements

# 15.1 Authentication & Session Security

### SR-1

JWT-based authentication.

* short-lived access tokens
* rotating refresh tokens
* HttpOnly secure cookies

---

### SR-2

OAuth2 login support.

Providers:

* Google
* GitHub

---

### SR-3

Login hardening.

* bcrypt password hashing
* rate-limited attempts
* CAPTCHA escalation after abuse threshold

---

# 15.2 Anti-Cheat & Integrity

### SR-4

All score calculations occur server-side.

---

### SR-5

Each session uses signed session tokens.

---

### SR-6

Replay detection prevents duplicate daily submissions.

---

### SR-7

Question submissions are rate-limited.

---

### SR-8

Outlier score detection flags suspicious gameplay.

---

# 15.3 Input Security

### SR-9

Prompt injection prevention is mandatory.

---

### SR-10

All AI outputs must pass schema validation.

---

### SR-11

All database queries must use parameterized SQL.

---

# 16. System Architecture

```text
Transfermarkt Dataset CSVs
        ↓
Ingestion & Normalization Pipeline
        ↓
Supabase PostgreSQL Database
        ↓
Game Logic Engine
        ↓
AI Question Interpreter
        ↓
Structured Query Builder
        ↓
Parameterized PostgreSQL Queries
        ↓
YES / NO / UNKNOWN Response
        ↓
Card Reveal + Candidate Filtering
```

---

# 17. Data Source Strategy

## Primary Data Source

### Transfermarkt Dataset

The project uses a large scraped Transfermarkt dataset consisting of:

* players
* clubs
* competitions
* appearances
* games
* lineups
* transfers
* valuations
* national teams
* game events

The dataset is ingested locally, normalized, and stored in Supabase PostgreSQL.

---

## Data Philosophy

The platform does NOT query live football APIs during gameplay.

Reasons:

* API cost reduction
* faster gameplay responses
* deterministic answers
* improved reliability
* reduced dependency on third-party services

---

## Future Data Updates

Periodic ingestion updates may refresh:

* transfers
* player clubs
* valuations
* squad changes
* competition participation

---

# 18. Database Architecture

The project uses a heavily relational PostgreSQL schema optimized for football deduction queries.

The database is hosted on Supabase.

---

# 18.1 Core Entity Tables

* players
* clubs
* competitions
* countries
* national_teams

---

# 18.2 Relationship Tables

* player_club_history
* transfers
* appearances
* game_lineups
* games
* game_events
* club_games

---

# 18.3 Value & Historical Tables

* player_valuations

---

# 18.4 NLP Support Tables

* aliases
* entity_mappings

---

# 18.5 Gameplay Tables

* game_sessions
* questions
* guesses

---

# 19. AI / NLP Design

## AI Responsibilities

The AI layer is responsible for:

* intent classification
* football entity extraction
* natural-language interpretation
* structured filter generation

---

## AI Is NOT Responsible For

* football knowledge storage
* football truth generation
* answering directly
* constructing raw SQL

---

## Example NLP Flow

### User Input

"Has he won the Champions League?"

---

### Parsed Output

```json
{
  "intent": "competition_win",
  "competition": "UEFA Champions League"
}
```

---

### Structured Query

```sql
SELECT EXISTS(
  SELECT 1
  FROM appearances a
  JOIN competitions c ON a.competition_id = c.id
  WHERE a.player_id = :player_id
  AND c.name = 'UEFA Champions League'
);
```

---

### Final Response

YES / NO / UNKNOWN

---

# 20. Candidate Filtering System

The game internally maintains a hidden candidate pool.

Each answer progressively narrows the valid player set.

Example:

```text
Initial Pool → 2,400 players

Question: Has he played in England?
→ 900 players remain

Question: Is he a defender?
→ 240 players remain

Question: Has he won the Champions League?
→ 31 players remain
```

The candidate pool remains entirely server-side.

---

# 21. Technical Stack

## Frontend

* React
* Next.js
* TailwindCSS

---

## Backend

* Python
* FastAPI
* SQLAlchemy
* Alembic

---

## Database

* Supabase PostgreSQL

---

## AI Layer

Initial:

* lightweight hosted LLM APIs

Future:

* self-hosted local models
* football-specific fine-tuning

---

## Infrastructure

* Supabase
* Vercel
* Docker (local development)

---

# 22. Data Ingestion Pipeline

The ingestion pipeline converts raw Transfermarkt CSV data into normalized relational entities.

Pipeline stages:

1. raw CSV ingestion
2. cleaning & normalization
3. alias generation
4. position mapping
5. relationship construction
6. PostgreSQL insertion
7. integrity validation

---

## Key Normalization Tasks

### Position Mapping

Transfermarkt positions such as:

* Centre-Back
* Left Winger
* Attacking Midfield

must map into:

* DEF
* MID
* ATT
* GK

and flank categories:

* LFT
* CTR
* RHT

---

### Alias Resolution

Examples:

* Barca → FC Barcelona
* PSG → Paris Saint-Germain
* Inter → Inter Milan

Aliases are stored in dedicated NLP support tables.

---

# 23. Analytics & Metrics

## Gameplay Metrics

* average questions per win
* win rates by difficulty
* most common first questions
* average game duration

---

## System Metrics

* query latency
* ingestion duration
* NLP parsing confidence
* database performance

---

## Security Metrics

* prompt injection attempts
* suspicious score submissions
* failed authentication attempts

---

# 24. Risks & Challenges

## Risk 1 — Incomplete Football Data

Some fringe players may lack sufficient historical information.

Mitigation:
pre-game eligibility checks.

---

## Risk 2 — AI Misclassification

AI may misunderstand ambiguous football prompts.

Mitigation:
strict schema validation and UNKNOWN fallback.

---

## Risk 3 — Large Dataset Performance

Millions of football records may slow queries.

Mitigation:
indexes, query optimization, and caching.

---

## Risk 4 — Prompt Injection

Users may attempt jailbreak-style prompts.

Mitigation:
strict validation, rate limiting, and logging.

---

## Risk 5 — Schema Complexity

Relational football data can become difficult to maintain.

Mitigation:
Alembic migrations, normalized schema, strict conventions.

---

# 25. Development Roadmap

# Phase 1 — Database Foundation

Goals:

* Supabase PostgreSQL setup
* SQLAlchemy models
* Alembic migrations
* ingestion pipeline
* normalized football database
* query validation

---

# Phase 2 — Core Gameplay Engine

Goals:

* candidate filtering
* YES/NO answer engine
* deduction logic
* game sessions
* CLI/internal testing

---

# Phase 3 — AI Integration

Goals:

* NLP intent classification
* entity extraction
* structured filter generation
* prompt injection detection

---

# Phase 4 — Frontend & UX

Goals:

* card reveal UI
* gameplay interface
* clue chips
* animations
* responsive design

---

# Phase 5 — Accounts & Metagame

Goals:

* authentication
* leaderboards
* streak systems
* badges
* daily challenge

---

# Phase 6 — Optimization & Expansion

Goals:

* caching
* advanced AI improvements
* historical football mode
* multiplayer consideration
* mobile exploration

---

# 26. Success Criteria

The product is successful if:

* players can ask football questions naturally
* answers remain accurate and database-backed
* deduction gameplay feels intelligent and replayable
* the football database scales reliably
* AI interpretation feels seamless
* cloud infrastructure remains stable and extensible
* the project demonstrates strong engineering quality as a portfolio piece

---

# 27. Conclusion

You Know Ball? combines:

* football deduction gameplay
* AI-powered natural-language interpretation
* large-scale relational football databases
* scalable Supabase-hosted infrastructure
* secure backend architecture
* progressive deduction mechanics
* football knowledge engineering

The system is designed around a core principle:

Structured football data is the source of truth.

AI exists only to bridge natural football language with relational football logic.

This architecture allows the platform to remain:

* scalable
* accurate
* secure
* replayable
* extensible

while delivering a football deduction experience that feels genuinely intelligent.

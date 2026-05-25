# You Know Ball?

Version: 2.0
Status: Draft
Project Type: AI-Powered Football Trivia Platform

---

# 1. Executive Summary

You Know Ball? is an AI-powered football trivia and deduction platform where users attempt to identify a hidden football player by asking open-ended yes/no questions.

Unlike traditional trivia games with predefined questions, the platform allows users to ask natural-language football questions such as:

- "Has he played in the Premier League?"
- "Is he Brazilian?"
- "Has he won the Champions League?"
- "Did he play with Cristiano Ronaldo?"
- "Has he scored more than 100 goals?"

The system interprets the question using AI, queries a structured football database, and responds with:

- YES
- NO
- UNKNOWN

The project combines:
- football data engineering
- AI-powered language interpretation
- database querying
- game logic
- football trivia gameplay

---

# 2. Problem Statement

Current football trivia games are limited because:

- questions are predefined
- gameplay is repetitive
- football knowledge depth is shallow
- there is little personalization
- users cannot ask open-ended questions

Football fans enjoy proving football knowledge socially.

There is an opportunity to create a dynamic football trivia system where:
- users can ask almost any football-related question
- AI interprets questions naturally
- answers are backed by structured football data
- gameplay feels intelligent and replayable

---

# 3. Product Vision

To create the most intelligent football trivia and deduction platform powered by real football data and natural-language interaction.

The platform should feel like:
- talking to a football analyst
- playing a football deduction game
- competing in a football IQ challenge

---

# 4. Goals & Objectives

## Primary Goals

### Goal 1 — Open-Ended Football Trivia
Allow users to ask natural yes/no questions about football players.

---

### Goal 2 — Accurate Responses
Ensure all answers are verified using structured football data.

---

### Goal 3 — Scalable Architecture
Build a system capable of supporting:
- thousands of players
- historical data
- future multiplayer support
- future real-time features

---

### Goal 4 — Engaging Gameplay
Create gameplay that rewards football knowledge and deduction skills.

---

# 5. Non-Goals

The following are NOT initial priorities:

- Live football scores
- Real-time match tracking
- Fantasy football integration
- Betting systems
- AI-generated football commentary
- Social networking platform
- Mobile apps (initially)

---

# 6. Target Audience

## Primary Users

### Football Fans
Users who enjoy football trivia and football knowledge games.

---

### Football Twitter / Online Football Communities
Users who enjoy debates, football knowledge challenges, and sports discussions.

---

### Casual Gamers
Players who enjoy deduction-style games such as:
- Wordle
- GeoGuessr
- Loldle
- 20 Questions

---

### Developers / Recruiters
The project also serves as a technical portfolio project demonstrating:
- AI integration
- database engineering
- NLP systems
- scalable backend design
- applied cybersecurity (auth, anti-cheat, secure leaderboard)

---

# 7. User Stories

## Gameplay

### User Story 1
As a player, I want to ask natural yes/no football questions so that gameplay feels dynamic.

---

### User Story 2
As a player, I want accurate responses based on real football data.

---

### User Story 3
As a player, I want to eventually identify the hidden football player.

---

### User Story 4
As a player, I want my previous questions displayed so I can track deductions.

---

### User Story 5
As a player, I want multiple difficulty modes that match my football knowledge level.

---

### User Story 6
As a player, I want to see what I have confirmed about the player — position, flank, nationality, club — displayed on the card as I narrow down.

---

### User Story 7
As a player, I want to compete on a leaderboard against friends and globally.

---

### User Story 8
As a player, I want a daily challenge that resets every 24 hours and lets me share my result.

---

# 8. Core Gameplay Loop

## Gameplay Flow

1. Player selects difficulty mode
2. System selects hidden player from the appropriate pool
3. Player asks a yes/no football question
4. AI interprets the question
5. Backend converts question into structured logic
6. Database verifies answer
7. System returns YES / NO / UNKNOWN
8. Confirmed information (position, flank, nationality, club) is revealed on the card
9. Other answers stack as clue chips
10. Player continues until correct guess or 20 questions exhausted

---

# 9. Player Pool & Difficulty Modes

## Scope

Initial release covers active players currently registered in the top 5 European leagues:

- Premier League
- La Liga
- Bundesliga
- Serie A
- Ligue 1

Historical players and retired players are out of scope for v1.

---

## 9.1 Reel Watcher (Easy)

**Definition:** Players from the top 4 clubs per league, filtered to those with 500+ minutes played in the current season.

**Rationale:** Filters out squad fillers who technically belong to a top club but are not widely recognised. Ensures every player in this pool is someone a casual fan would know.

**Approximate pool size:** 300–400 players

| League | Clubs included | Approx. players |
|---|---|---|
| Premier League | Top 4 | ~80 |
| La Liga | Top 4 | ~80 |
| Bundesliga | Top 4 | ~80 |
| Serie A | Top 4 | ~80 |
| Ligue 1 | Top 4 | ~80 |

---

## 9.2 Mid (Medium)

**Definition:** Players from the top 6 clubs per league, filtered to those with 500+ minutes played in the current season.

**Approximate pool size:** 500–600 players

| League | Clubs included | Approx. players |
|---|---|---|
| Premier League | Top 6 | ~120 |
| La Liga | Top 6 | ~120 |
| Bundesliga | Top 6 | ~120 |
| Serie A | Top 6 | ~120 |
| Ligue 1 | Top 6 | ~120 |

---

## 9.3 Ball Knower (Hard)

**Definition:** All registered squad players across all clubs in all 5 leagues. No appearance filter applied. Includes squad players, bench warmers, and youth call-ups.

**Approximate pool size:** 2,200–2,400 players

| League | Approx. players |
|---|---|
| Premier League | ~530 |
| La Liga | ~500 |
| Bundesliga | ~450 |
| Serie A | ~500 |
| Ligue 1 | ~420 |

---

## Pool Behaviour

- Modes are cumulative. Ball Knower includes all Mid players. Mid includes all Reel Watcher players.
- Player selection within a mode is weighted. Reel Watcher will not randomly select a fringe squad player even if one technically qualifies.
- The daily challenge uses a fixed mode. Mode is not selectable for daily — it rotates on a weekly schedule (Easy → Medium → Hard → repeat).

---

## Player Selection Algorithm

The system must guarantee that every selected player has sufficient data to be answerable. Before selecting a player for a session the system checks:

- nationality is populated
- current club is populated
- position is populated
- at least one season of statistics exists
- at least one league or club history entry exists

Players failing this check are excluded from selection regardless of mode.

---

# 10. Functional Requirements

## 10.1 User Input System

### FR-1
Users must be able to type open-ended football questions (max 200 characters).

---

### FR-2
The system must support flexible phrasing.

Examples:
- "Did he ever play for Barca?"
- "Has he played in Spain?"
- "Is he under 30?"

---

### FR-3
Questions must be validated before processing.

Invalid questions:
- non-football questions
- offensive prompts
- ambiguous nonsense
- questions exceeding 200 characters

---

### FR-4
The system must limit question submissions to one per two seconds per session to prevent scripted querying.

---

## 10.2 AI Question Interpreter

### FR-5
AI must classify question intent.

Possible intent categories:
- nationality
- club history
- league history
- trophies
- statistics
- age
- position
- flank / playing side
- teammates
- international career

---

### FR-6
AI must extract entities.

Example:

Question: "Has he played for Real Madrid?"

Extracted:
```json
{
  "type": "club_history",
  "club": "Real Madrid"
}
```

---

### FR-7
AI must NOT directly answer football questions.

AI only interprets questions. Database determines truth.

---

### FR-8
AI output must be validated against a strict JSON schema before being used to construct a database query. Malformed or unexpected output is rejected.

---

### FR-9
Prompt injection attempts must be detected, rejected, and logged for review.

---

## 10.3 Card Reveal System

The player card displays confirmed information progressively as the player answers questions. All fields start hidden and are only revealed on a confirmed YES answer to the relevant question type.

### FR-10
The card must display the following fields:

| Field | Location on card | Revealed by |
|---|---|---|
| Position (DEF / MID / ATK / GK) | Left panel, top box | YES answer to a position question |
| Flank (LFT / CTR / RHT) | Left panel, bottom box | YES answer to a flank question |
| Nationality | Right panel, top box | YES answer to a nationality question |
| Current club | Right panel, bottom box | YES answer to a current club question |
| Player silhouette | Centre | Correct final guess only |

---

### FR-11
If the player is confirmed as GK, the flank box must automatically lock and display "—". Goalkeepers have no flank assignment.

---

### FR-12
Boxes remain hidden (displaying "?") on NO or UNKNOWN answers. A box is only filled when the answer is a confirmed YES.

---

### FR-13
If two separate position questions both receive YES (e.g. "Is he a midfielder?" YES, then "Is he an attacker?" NO), only the confirmed YES populates the box. The most recently confirmed YES overwrites the previous.

---

## 10.4 Database Query System

### FR-14
Backend must generate structured parameterized database queries from validated AI output.

---

### FR-15
All responses must be derived from stored data. The AI never answers directly.

---

### FR-16
The system must support:
- player history queries
- statistics queries
- trophy queries
- league queries
- relational football queries (teammates, opponents)

---

## 10.5 Response System

### FR-17
The system must respond with: YES / NO / UNKNOWN

---

### FR-18
Optional explanation mode may display supporting context.

Example: "Yes — the player played for Juventus between 2018 and 2021."

---

## 10.6 Game State Management

### FR-19
The system must track per session:
- previous questions and answers
- number of attempts (max 20)
- elapsed time (server-side clock)
- hidden player identity
- current card reveal state

---

### FR-20
The hidden player must remain consistent and tamper-proof during a session. The player identity is stored server-side only and is never exposed to the client until a correct guess or game end.

---

### FR-21
The system must support game resets without exposing the previous player.

---

## 10.7 Win & Loss Flow

### Win condition
Player submits a correct guess at any point within 20 questions.

### Loss condition
Player exhausts all 20 questions without a correct guess.

### Win flow
1. Player silhouette revealed and transitions from dark to coloured
2. Win modal displayed showing: player name, score, questions used, time taken
3. Daily result card generated (spoiler-free emoji pattern)
4. Share prompt shown
5. Leaderboard displayed with new rank highlighted
6. Option to play again or try next difficulty

### Loss flow
1. Player identity revealed
2. Score of 0 recorded — no leaderboard submission
3. Guess streak resets to 0
4. "Study this player" option shown — displays player career summary so the user learns

---

# 11. Scoring System

Score is calculated entirely server-side using server timestamps. The client never performs score calculations.

```
base_score         = 1000
question_penalty   = questions_asked × 40
time_penalty       = floor(elapsed_seconds / 30) × 10
difficulty_bonus   = Reel Watcher: 0 / Mid: +200 / Ball Knower: +500
streak_multiplier  = 1 + (guess_streak × 0.05)

final_score = (base_score − question_penalty − time_penalty + difficulty_bonus) × streak_multiplier
```

Minimum score on a win is 50 (score cannot go below 50 for a correct guess regardless of penalties).

Scores are only submitted to the leaderboard on a win. Losses do not generate a score entry.

---

# 12. Streak & Metagame Systems

## 12.1 Daily Streak

- Increments when the player completes at least one game per calendar day (UTC)
- Resets to 0 if a day is missed without a streak freeze token
- Displayed as a flame counter in the game header

### Streak milestones

| Days | Reward |
|---|---|
| 3 | Bronze badge |
| 7 | Streak freeze token granted |
| 14 | Silver badge |
| 30 | Gold badge + "On fire" achievement |
| 100 | Platinum badge |

---

## 12.2 Guess Streak

- Increments on every correct guess regardless of day
- Resets only on a wrong final guess (loss)
- Feeds into the score multiplier
- Displayed on the player profile

---

## 12.3 Streak Freeze

- Earned at every 7-day daily streak milestone
- Spends automatically when a day is missed
- Maximum 2 tokens stored at once
- Displayed as a shield icon next to the flame counter

---

## 12.4 Badge System

Badges are earned through gameplay, not purchased.

| Badge | Condition |
|---|---|
| One question wonder | Correct guess in 1 question |
| Legend hunter | 10 Ball Knower correct guesses |
| On fire | 30-day daily streak |
| Tactician | Correct guess without asking nationality |
| Daily dominator | Rank 1 on a daily challenge leaderboard |
| Ironclad | 100-day daily streak |

---

## 12.5 Daily Challenge

- One hidden player per day, identical for all users worldwide
- Mode rotates weekly: Easy → Medium → Hard → repeat
- Resets at midnight UTC
- After solving, a shareable result card is generated
- Result card format: spoiler-free emoji row (YES = checkmark, NO = cross, UNKNOWN = question mark)
- Player name is hidden in shared text until the recipient plays
- Share text format: "You Know Ball? Daily #[N] — solved in [X] questions. Can you beat me?"

---

# 13. Leaderboard System

Leaderboard details to be fully specified in a future revision. High-level structure:

## Three tabs

- **Global** — top 1000 all-time, refreshed hourly (not real-time). Player's own rank always pinned at the bottom even if outside top 1000.
- **Friends** — scores visible only to mutual friends. Friends added by username or signed invite link.
- **Daily** — resets with each daily challenge. Ranked by score, time as tiebreaker.

---

# 14. Non-Functional Requirements

## 14.1 Performance

### NFR-1
Responses should return within 1–2 seconds.

### NFR-2
The database should support thousands of concurrent queries.

---

## 14.2 Scalability

### NFR-3
The system should support future expansion to:
- additional leagues
- historical datasets
- multiplayer modes
- mobile applications

---

## 14.3 Reliability

### NFR-4
The system should avoid hallucinated football information. All answers must be database-backed.

---

# 15. Security Requirements

Security is a first-class concern given the project's portfolio purpose in demonstrating applied cybersecurity.

## 15.1 Authentication & Session Security

### SR-1 — JWT pattern
- Access tokens: short-lived (15 minute expiry), stored in memory only — never in localStorage
- Refresh tokens: stored as HttpOnly; Secure; SameSite=Strict cookies
- Token rotation on every refresh — old token invalidated immediately on use

### SR-2 — Login hardening
- OAuth2 (Google / GitHub) as primary login method
- Email/password as fallback — passwords hashed with bcrypt at cost factor 12
- Login attempts rate-limited: 5 attempts per 15 minutes per IP, CAPTCHA required after threshold

---

## 15.2 Anti-Cheat & Tamper Detection

### SR-3 — Server-side scoring
- Score is never calculated client-side
- All score math uses server-recorded timestamps
- Client submits session token + guess only — server computes the score

### SR-4 — Session integrity
- Each game session has a signed session_token issued at game start
- Score submissions without a valid matching session_token are rejected
- Replay detection: a player cannot submit a score for the same daily puzzle twice

### SR-5 — Rate limiting
- Question submissions: max 1 per 2 seconds per session
- Score submissions: max 1 per completed game session

### SR-6 — Outlier detection
- Statistical flag on scores that are mathematically implausible (e.g. maximum score in under 20 seconds)
- Flagged scores held for admin review before appearing on leaderboard

---

## 15.3 Secure Leaderboard

### SR-7 — Audit log
- Every score submission records: user ID, IP address, user agent, session duration, question count, timestamp
- Log is append-only

### SR-8 — Access control
- Leaderboard endpoints require a valid authenticated session
- No public unauthenticated access to score data

### SR-9 — Signed invite links
- Friend invite links are HMAC-signed with user_id + expiry timestamp
- Links expire after 24 hours and cannot be forged or extended

---

## 15.4 Input Security

### SR-10 — Prompt injection prevention
- User question input is sanitised before being passed to the AI layer
- AI output is validated against a strict JSON schema before any DB query is constructed
- Input capped at 200 characters
- Injection attempts logged and flagged for review

### SR-11 — SQL injection prevention
- All database queries use parameterized statements
- The AI layer never constructs or touches raw SQL

---

# 16. System Architecture

```
Top 5 League APIs / Datasets
          ↓
Data Ingestion Pipeline (scheduled, periodic)
          ↓
PostgreSQL Database
          ↓
Game Logic Engine  ←→  Session Manager (server-side state)
          ↓
AI Question Interpreter (intent classification + entity extraction)
          ↓
Parameterized DB Query Builder
          ↓
YES / NO / UNKNOWN Response
          ↓
Card Reveal State Update
```

---

# 17. Data Sources

## Primary Source

### API-Football
Used for:
- players
- clubs
- transfers
- statistics
- leagues
- trophies

---

## Secondary Sources

### Transfermarkt Data
Used for:
- detailed transfer history
- market value
- career progression

### Kaggle / Open Datasets
Used for:
- initial seeding
- testing
- historical bulk imports

---

# 18. Database Schema

## 18.1 Players

```sql
Players (
  id,
  name,
  nationality,
  birth_date,
  position,           -- DEF | MID | ATK | GK
  flank,              -- LFT | CTR | RHT | NULL (GK)
  current_club_id,
  dominant_foot,
  height,
  is_active,          -- boolean
  minutes_current_season
)
```

---

## 18.2 Clubs

```sql
Clubs (
  id,
  name,
  country,
  league,
  current_league_position
)
```

---

## 18.3 Club History

```sql
PlayerClubHistory (
  player_id,
  club_id,
  start_year,
  end_year,
  is_loan,            -- boolean
  appearances,
  goals,
  assists,
  minutes_played
)
```

---

## 18.4 Season Statistics

```sql
SeasonStats (
  player_id,
  season,
  competition,
  goals,
  assists,
  minutes_played,
  appearances
)
```

---

## 18.5 National Team Statistics

```sql
NationalTeamStats (
  player_id,
  country,
  caps,
  goals,
  debut_year,
  tournaments
)
```

---

## 18.6 Trophies

```sql
PlayerTrophies (
  player_id,
  trophy_name,
  year,
  club_id
)
```

---

# 19. AI / NLP Design

## AI Responsibilities

- natural-language understanding
- entity extraction
- question classification
- structured query generation

## AI is NOT responsible for

- football knowledge storage
- direct answering
- statistical truth generation
- raw SQL construction

---

## Example NLP Flow

**User question:** "Has he won a Ballon d'Or?"

**Parsed intent:**
```json
{
  "type": "trophy_check",
  "trophy": "Ballon d'Or"
}
```

**Database query:**
```sql
SELECT *
FROM PlayerTrophies
WHERE player_id = ?
AND trophy_name = 'Ballon d''Or';
```

**Response:** YES / NO

---

## NLP Fallback Handling

If a question cannot be classified with sufficient confidence:
- The system returns an UNKNOWN response
- The question is logged for review
- The player is prompted to rephrase

Confidence threshold for intent classification: to be defined during Phase 2 implementation.

---

# 20. Candidate Filtering System

The game internally maintains a candidate pool. Each question narrows possible players.

```
Initial pool (mode-dependent)
  Reel Watcher → ~400 players
  Mid          → ~600 players
  Ball Knower  → ~2,400 players

Question 1: Has he played in England?
  → pool narrows to PL players only

Question 2: Is he a defender?
  → pool narrows further

Question 3: Has he won the Champions League?
  → pool narrows further
```

The candidate pool is tracked server-side. The client never sees pool size or contents.

---

# 21. UI Framework

Full UI specification to be developed separately. High-level framework:

## Card Layout

The central game element is a player card with the following zones:

- **Top bar** — game title, difficulty label
- **Left panel** — position box (DEF / MID / ATK / GK) and flank box (LFT / CTR / RHT), both hidden until confirmed
- **Centre** — blacked-out player silhouette, revealed only on correct guess
- **Right panel** — nationality box and current club box, both hidden until confirmed
- **Footer** — clue chip row, question dot tracker, question input, guess button

## Clue Chips

All non-card answers (league history, trophies, stats, teammates) stack as colour-coded chips below the card:
- Green = YES
- Red = NO
- Amber = UNKNOWN

## Question Tracker

20 dots displayed below the clue chips. Amber = question used. Green = correct guess dot.

## HUD

Persistent header showing: daily streak, question count (X / 20), elapsed time.

---

# 22. Technical Stack

## Frontend
- React
- Next.js
- TailwindCSS

## Backend
- Python FastAPI (preferred) or Node.js + Express

## Database
- PostgreSQL

## AI Layer
- OpenAI API (Phase 2)
- Local LLM (Phase 4 consideration)

## Hosting
- Vercel (frontend)
- Railway / Render / Supabase (backend + DB)

---

# 23. Analytics & Metrics

## Gameplay Metrics
- average questions per win per mode
- average session duration
- win rate per mode
- most common questions asked
- most common first questions

## System Metrics
- response latency
- DB query speed
- AI parsing accuracy
- API ingestion success rate

## Security Metrics
- flagged score submissions per day
- failed login attempts per hour
- prompt injection attempts per day

---

# 24. Risks & Challenges

## Risk 1 — Incomplete Data
Some players in Ball Knower mode may have sparse data making them unanswerable.

Mitigation: pre-game eligibility check on every candidate player before selection.

---

## Risk 2 — AI Hallucination
AI may generate incorrect assumptions about player data.

Mitigation: AI only interprets. Database determines truth.

---

## Risk 3 — Query Ambiguity
Some questions may map to multiple intent categories.

Mitigation: confidence thresholds, fallback to UNKNOWN, log for review.

---

## Risk 4 — API Costs
Large-scale football data APIs can be expensive at scale.

Mitigation: local caching, periodic ingestion, query against local DB only during gameplay.

---

## Risk 5 — Score Manipulation
Players may attempt to fake scores or inflate leaderboard positions.

Mitigation: server-side scoring, signed session tokens, audit log, outlier detection.

---

# 25. Development Phases

## Phase 1 — Prototype

Goals:
- PostgreSQL schema setup
- API-Football ingestion for top 5 leagues (current season)
- Player eligibility checker
- Simple yes/no logic (no AI — keyword matching only)
- Basic card UI (position, flank, nation, club reveal)
- Win / loss flow

---

## Phase 2 — AI Integration

Goals:
- NLP intent classification
- Entity extraction
- Flexible question handling
- Confidence threshold + fallback handling
- Prompt injection detection

---

## Phase 3 — Metagame & Leaderboard

Goals:
- JWT auth + OAuth2
- Daily streak system
- Guess streak + score multiplier
- Leaderboard (global, friends, daily)
- Badge system
- Daily challenge + shareable result card
- Anti-cheat: session token, server-side scoring, audit log

---

## Phase 4 — Expansion & Optimisation

Goals:
- Caching layer
- Scaling
- Improved AI accuracy
- Outlier detection and admin review dashboard
- Historical player mode (post-v1)
- Mobile application consideration

---

# 26. Success Criteria

The product is successful if:

- players can ask flexible football questions naturally
- answers are accurate and data-backed
- the card reveal system makes deduction visually satisfying
- gameplay feels intelligent and replayable across all three difficulty modes
- the leaderboard and streak systems drive return sessions
- the security implementation is robust enough to demonstrate in a portfolio context

---

# 27. Conclusion

You Know Ball? combines:
- football trivia and deduction gameplay
- AI-driven natural-language interpretation
- structured football data engineering
- a progressive card reveal UI
- scalable backend architecture
- applied cybersecurity across auth, anti-cheat, and leaderboard integrity

The recommended development approach emphasises:
- reliable structured data as the single source of truth
- AI limited strictly to interpretation
- security implemented as a first-class feature from Phase 1
- engaging progressive reveal mechanics that reward deduction over guessing
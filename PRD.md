# Product Requirements Document (PRD)

# You Know Ball?

Version: 1.0
Status: Draft
Project Type: AI-Powered Football Trivia Platform

---

# 1. Executive Summary

You Know Ball? is an AI-powered football trivia and deduction platform where users attempt to identify a hidden football player by asking open-ended yes/no questions.

Unlike traditional trivia games with predefined questions, the platform allows users to ask natural-language football questions such as:

- “Has he played in the Premier League?”
- “Is he Brazilian?”
- “Has he won the Champions League?”
- “Did he play with Cristiano Ronaldo?”
- “Has he scored more than 100 goals?”

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
As a player, I want multiple difficulty modes.

---

# 8. Core Gameplay Loop

## Gameplay Flow

1. System selects hidden player
2. User asks a yes/no football question
3. AI interprets the question
4. Backend converts question into structured logic
5. Database verifies answer
6. System returns YES/NO/UNKNOWN
7. User continues until player is identified

---

# 9. Functional Requirements

# 9.1 User Input System

## Requirements

### FR-1
Users must be able to type open-ended football questions.

---

### FR-2
The system must support flexible phrasing.

Examples:
- “Did he ever play for Barca?”
- “Has he played in Spain?”
- “Is he under 30?”

---

### FR-3
Questions must be validated before processing.

Invalid questions:
- non-football questions
- offensive prompts
- ambiguous nonsense

---

# 9.2 AI Question Interpreter

## Requirements

### FR-4
AI must classify question intent.

Possible intent categories:
- nationality
- club history
- league history
- trophies
- statistics
- age
- position
- teammates
- international career

---

### FR-5
AI must extract entities.

Example:

Question:
“Has he played for Real Madrid?”

Extracted:

```json
{
  "type": "club_history",
  "club": "Real Madrid"
}
```

---

### FR-6
AI must NOT directly answer football questions.

AI only interprets questions.

Database determines truth.

---

# 9.3 Database Query System

## Requirements

### FR-7
Backend must generate structured database queries.

---

### FR-8
All responses must be derived from stored data.

---

### FR-9
The system must support:
- player history queries
- statistics queries
- trophy queries
- league queries
- relational football queries

---

# 9.4 Response System

## Requirements

### FR-10
The system must respond with:
- YES
- NO
- UNKNOWN

---

### FR-11
Optional explanation mode may display supporting data.

Example:

“Yes — the player played for Juventus between 2018 and 2021.”

---

# 9.5 Game State Management

## Requirements

### FR-12
The system must track:
- previous questions
- previous answers
- number of attempts
- game duration

---

### FR-13
The system must support game resets.

---

### FR-14
The hidden player must remain consistent during a session.

---

# 9.6 Difficulty Modes

## Easy
Current top 5 league players.

---

## Medium
Includes recent retired players.

---

## Hard
Includes obscure or historical footballers.

---

# 10. Non-Functional Requirements

# 10.1 Performance

### NFR-1
Responses should return within 1–2 seconds.

---

### NFR-2
The database should support thousands of concurrent queries.

---

# 10.2 Scalability

### NFR-3
The system should support future expansion to:
- additional leagues
- historical datasets
- multiplayer modes
- mobile applications

---

# 10.3 Reliability

### NFR-4
The system should avoid hallucinated football information.

All answers must be database-backed.

---

# 10.4 Security

### NFR-5
Prevent:
- prompt injection
- malicious queries
- unrestricted SQL execution

---

### NFR-6
All database queries must be parameterized.

---

# 11. System Architecture

# High-Level Architecture

```text
Football APIs / Datasets
          ↓
Data Ingestion Pipeline
          ↓
PostgreSQL Database
          ↓
Game Logic Engine
          ↓
AI Question Interpreter
          ↓
YES / NO Response
```

---

# 12. Data Sources

## Recommended Primary Source

### API-FOOTBALL

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
- market value history
- career progression

---

### Kaggle/Open Datasets
Used for:
- initial seeding
- testing
- historical bulk imports

---

# 13. Database Requirements

# 13.1 Players Table

```sql
Players (
  id,
  name,
  nationality,
  birth_date,
  position,
  current_club,
  dominant_foot,
  height
)
```

---

# 13.2 Clubs Table

```sql
Clubs (
  id,
  name,
  country,
  league
)
```

---

# 13.3 Club History

```sql
PlayerClubHistory (
  player_id,
  club_id,
  start_year,
  end_year,
  appearances,
  goals,
  assists,
  minutes_played
)
```

---

# 13.4 Season Statistics

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

# 13.5 National Team Statistics

```sql
NationalTeamStats (
  player_id,
  country,
  caps,
  goals,
  tournaments
)
```

---

# 13.6 Trophies

```sql
PlayerTrophies (
  player_id,
  trophy_name,
  year,
  club_id
)
```

---

# 14. AI/NLP Design

# AI Responsibilities

The AI layer is responsible for:
- natural-language understanding
- entity extraction
- question classification
- structured query generation

The AI is NOT responsible for:
- football knowledge storage
- direct answering
- statistical truth generation

---

# Example NLP Flow

## User Question

“Has he won a Ballon d’Or?”

---

## Parsed Intent

```json
{
  "type": "trophy_check",
  "trophy": "Ballon d'Or"
}
```

---

## Database Query

```sql
SELECT *
FROM PlayerTrophies
WHERE player_id = ?
AND trophy_name = 'Ballon d''Or';
```

---

## Response

YES / NO

---

# 15. Candidate Filtering System

The game internally maintains a candidate pool.

Each question narrows possible players.

Example:

```text
Initial pool → 10,000 players
```

Questions reduce possibilities.

Example:

```text
Question 1:
Has he played in England?
→ 4,200 players remain

Question 2:
Is he a defender?
→ 900 players remain

Question 3:
Has he won the Champions League?
→ 110 players remain
```

---

# 16. UI/UX Requirements

# Core UI Components

## Question Input
Text field for user questions.

---

## Answer Display
Shows:
- YES
- NO
- UNKNOWN

---

## Question History
Displays all previous questions and answers.

---

## Game Stats
Displays:
- question count
- elapsed time
- streaks

---

## Guess Submission
Allows player to submit final answer.

---

# 17. Future Features

## Multiplayer Mode
Multiple players compete in real-time.

---

## Daily Challenge
One hidden player per day.

---

## AI Hint System
AI suggests useful narrowing questions.

---

## Leaderboards
Track football knowledge rankings.

---

## Voice Questions
Allow spoken football questions.

---

## Historical Modes
Specific eras:
- 2000s football
- World Cup legends
- Premier League only

---

# 18. Technical Stack

## Frontend
- React
- Next.js
- TailwindCSS

---

## Backend
- Node.js + Express
OR
- Python FastAPI

---

## Database
- PostgreSQL

---

## AI Layer
- OpenAI API
- Local LLM later

---

## Hosting
- Vercel (frontend)
- Railway/Render/Supabase (backend + DB)

---

# 19. Analytics & Metrics

# Key Metrics

## Gameplay Metrics
- average questions per win
- average session duration
- win rate
- most common questions

---

## System Metrics
- response latency
- DB query speed
- AI parsing accuracy
- API ingestion success rate

---

# 20. Risks & Challenges

## Risk 1 — Incomplete Data
Some APIs may lack historical information.

Mitigation:
- combine multiple data sources
- support UNKNOWN responses

---

## Risk 2 — AI Hallucination
AI may generate incorrect assumptions.

Mitigation:
- AI only interprets
- database determines truth

---

## Risk 3 — Query Ambiguity
Some questions may be unclear.

Mitigation:
- ask follow-up clarification questions
- confidence thresholds

---

## Risk 4 — API Costs
Large-scale data APIs can become expensive.

Mitigation:
- local caching
- periodic ingestion
- local DB querying

---

# 21. Development Phases

# Phase 1 — Prototype

Goals:
- database setup
- player ingestion
- simple yes/no logic
- basic UI

---

# Phase 2 — AI Integration

Goals:
- NLP parsing
- entity extraction
- flexible question handling

---

# Phase 3 — Expansion

Goals:
- larger datasets
- multiplayer
- analytics
- leaderboards

---

# Phase 4 — Optimization

Goals:
- caching
- scaling
- improved AI accuracy
- production deployment

---

# 22. Success Criteria

The product is successful if:

- users can ask flexible football questions naturally
- answers are accurate and data-backed
- gameplay feels intelligent and engaging
- the system scales reliably
- players return for repeated sessions

---

# 23. Final Recommendation

Recommended architecture:

- API-Football for ingestion
- PostgreSQL as primary truth database
- AI only for interpretation
- backend-controlled query generation

This ensures:
- accuracy
- low latency
- scalability
- maintainability
- extensibility

---

# 24. Conclusion

You Know Ball? combines:
- football trivia
- AI-driven language interpretation
- structured football intelligence
- deduction gameplay
- scalable backend engineering

The project has the potential to evolve into:
- a football trivia platform
- a football IQ challenge system
- a multiplayer football knowledge game
- a sports-data engineering showcase

The recommended development approach emphasizes:
- reliable structured data
- AI-assisted interpretation
- scalable architecture
- engaging gameplay mechanics
- accurate football knowledge verification


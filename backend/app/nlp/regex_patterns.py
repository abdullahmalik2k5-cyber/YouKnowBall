"""Rule-based question parser.

Layer 1 of the two-stage parser. Handles common, well-structured football
questions locally with zero API latency. Falls through to the Groq LLM
for anything it cannot confidently classify.

Supported question types:
  - position     (Is he a striker? Is he a defender?)
  - nationality  (Is he Brazilian? Is he from Spain?)
  - continent    (Is he European? Is he African?)
  - age          (Is he under 30? Is he older than 25?)
  - foot         (Is he left-footed? Does he use his right foot?)
  - competition  (Has he played in La Liga? Did he play in the UCL?)
  - current_club (Does he play for Chelsea? Is his club Real Madrid?)
  - club_history (Did he ever play for Arsenal? Has he played for Barca?)
"""

import re
from sqlalchemy import text
from sqlalchemy.orm import Session

# ─── Static lookup tables ──────────────────────────────────────────────────────

# Demonym → standard country name
DEMONYMS: dict[str, str] = {
    "english": "England", "french": "France", "german": "Germany", "italian": "Italy",
    "spanish": "Spain", "brazilian": "Brazil", "argentine": "Argentina",
    "argentinian": "Argentina", "portuguese": "Portugal", "dutch": "Netherlands",
    "belgian": "Belgium", "croatian": "Croatia", "uruguayan": "Uruguay",
    "senegalese": "Senegal", "moroccan": "Morocco", "egyptian": "Egypt",
    "japanese": "Japan", "korean": "South Korea", "south korean": "South Korea",
    "polish": "Poland", "swiss": "Switzerland", "swedish": "Sweden",
    "norwegian": "Norway", "danish": "Denmark", "austrian": "Austria",
    "turkish": "Turkey", "scottish": "Scotland", "welsh": "Wales",
    "irish": "Ireland", "algerian": "Algeria", "nigerian": "Nigeria",
    "ghanaian": "Ghana", "colombian": "Colombia", "chilean": "Chile",
    "mexican": "Mexico", "greek": "Greece", "ukrainian": "Ukraine",
    "russian": "Russia", "serbian": "Serbia", "romanian": "Romania",
    "hungarian": "Hungary", "czech": "Czech Republic", "slovakian": "Slovakia",
    "slovenian": "Slovenia", "icelandic": "Iceland", "finnish": "Finland",
    "american": "United States", "cameroonian": "Cameroon",
    "ivorian": "Ivory Coast", "malian": "Mali", "guinean": "Guinea",
    "tunisian": "Tunisia", "congolese": "Democratic Republic of Congo",
    "gabonese": "Gabon", "togolese": "Togo", "burkinabe": "Burkina Faso",
    "iranian": "Iran", "saudi": "Saudi Arabia", "australian": "Australia",
    "jamaican": "Jamaica", "costa rican": "Costa Rica",
    "trinidadian": "Trinidad and Tobago",
}

# Continent demonyms / names → canonical continent name
CONTINENT_DEMONYMS: dict[str, str] = {
    "european": "Europe",
    "europe": "Europe",
    "african": "Africa",
    "africa": "Africa",
    "south american": "South America",
    "south america": "South America",
    "latin american": "South America",
    "latin": "South America",
    "north american": "North America",
    "north america": "North America",
    "central american": "North America",
    "asian": "Asia",
    "asia": "Asia",
    "middle eastern": "Asia",
    "oceanian": "Oceania",
    "oceania": "Oceania",
}

# Position keywords → position_group codes used in DB
POSITIONS: dict[str, str] = {
    "goalkeeper": "GK", "gk": "GK", "keeper": "GK", "goalie": "GK",
    "goalkeepers": "GK", "shot stopper": "GK",
    "defender": "DEF", "def": "DEF", "centerback": "DEF", "centre-back": "DEF",
    "center back": "DEF", "centre back": "DEF", "fullback": "DEF",
    "full-back": "DEF", "full back": "DEF", "left back": "DEF",
    "right back": "DEF", "wingback": "DEF", "defenders": "DEF",
    "midfielder": "MID", "mid": "MID", "midfielders": "MID",
    "central midfielder": "MID", "defensive midfielder": "MID",
    "attacking midfielder": "MID",
    "winger": "ATK", "wingers": "ATK", "forward": "ATK",
    "attacker": "ATK", "attackers": "ATK", "striker": "ATK",
    "strikers": "ATK", "centre forward": "ATK", "center forward": "ATK",
    "number 9": "ATK", "number 10": "MID",
}

# Club name aliases → canonical / search name
CLUB_ALIASES: dict[str, str] = {
    "barca": "FC Barcelona", "barcelona": "FC Barcelona",
    "real madrid": "Real Madrid", "madrid": "Real Madrid",
    "man city": "Manchester City", "manchester city": "Manchester City",
    "man united": "Manchester United", "man utd": "Manchester United",
    "manchester united": "Manchester United",
    "bayern": "Bayern Munich", "inter": "Inter Milan",
    "juve": "Juventus", "juventus": "Juventus",
    "arsenal": "Arsenal", "chelsea": "Chelsea",
    "liverpool": "Liverpool", "spurs": "Tottenham Hotspur",
    "tottenham": "Tottenham Hotspur", "psg": "Paris Saint-Germain",
    "dortmund": "Borussia Dortmund", "bvb": "Borussia Dortmund",
    "atletico": "Atletico Madrid", "atleti": "Atletico Madrid",
    "napoli": "SSC Napoli", "milan": "AC Milan", "ac milan": "AC Milan",
    "roma": "AS Roma", "lazio": "SS Lazio",
}

# Foot keywords → canonical foot value
FOOT_KEYWORDS: dict[str, str] = {
    "left foot": "left", "left-footed": "left", "left footed": "left",
    "his left": "left", "uses his left": "left", "left dominant": "left",
    "right foot": "right", "right-footed": "right", "right footed": "right",
    "his right": "right", "uses his right": "right", "right dominant": "right",
    "both feet": "both", "both-footed": "both", "two-footed": "both",
    "ambidextrous": "both", "weaker foot": "right",  # pragmatic default
}

# ─── Age regex ────────────────────────────────────────────────────────────────
# Captures patterns like: "under 30", "younger than 25", "over 32", "at least 28",
# "older than 33", "less than 27", "more than 29", "aged 31"
#
# IMPORTANT ordering rules:
#   1. "no less than" must come BEFORE "less than" (substring issue).
#   2. Patterns that start with digits (e.g. "30 or older") use a named group
#      (?P<years>\d) so extraction doesn't accidentally grab the word group.
#
AGE_PATTERNS = [
    # ≥ : "at least 30" / "no less than 25" / "minimum 28"
    (re.compile(r"\b(at least|no less than|minimum)\s+(?P<years>\d{1,2})\b"), "gte"),
    # ≥ : "30 or older" / "30 or more" / "30 or above"
    (re.compile(r"\b(?P<years>\d{1,2})\s+or\s+(?:older|more|above)\b"), "gte"),
    # ≤ : "30 or younger" / "30 or less" / "30 or below"
    (re.compile(r"\b(?P<years>\d{1,2})\s+or\s+(?:younger|less|below)\b"), "lte"),
    # < : "under 30" / "below 30" / "less than 30" / "younger than 30" / "not yet 30"
    (re.compile(r"\b(?:under|below|less than|younger than|not yet)\s+(?P<years>\d{1,2})\b"), "lt"),
    # > : "over 30" / "above 30" / "more than 30" / "older than 30" / "greater than 30"
    (re.compile(r"\b(?:over|above|more than|older than|greater than)\s+(?P<years>\d{1,2})\b"), "gt"),
    # = : "exactly 30" / "aged 30"
    (re.compile(r"\b(?:exactly|aged)\s+(?P<years>\d{1,2})\b"), "eq"),
    # = : "he's 30 years" / "he is 30 years"
    (re.compile(r"\bhe(?:'s| is)\s+(?P<years>\d{1,2})\s+years"), "eq"),
]


def parse_with_rules(db: Session, question: str) -> dict | None:
    """
    Uses regex and static lookup tables to parse simple, common questions
    with zero API latency.

    Returns a parsed dict or None if the rule engine cannot handle it.
    """
    q = question.lower().strip()

    # ── 0. Big Six — must come before any other check ────────────────────────
    # "is he in the big six", "does he play for a big 6 club", "big six club?" etc.
    # This is a club-group question, NOT a competition — handle it explicitly.
    if re.search(r"\bbig[\s\-]?6\b|\bbig[\s\-]?six\b", q):
        return {"type": "big_six", "value": "big_six"}

    # ── 1. Position ──────────────────────────────────────────────────────────
    for keyword, pos in POSITIONS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", q):
            return {"type": "position", "value": pos}


    # ── 2. Age ───────────────────────────────────────────────────────────────
    # Must come before nationality so "under 21" doesn't hit country detection.
    # All patterns use a named group 'years' for unambiguous digit extraction.
    for pattern, operator in AGE_PATTERNS:
        m = pattern.search(q)
        if m:
            years = int(m.group("years"))
            return {
                "type": "age",
                "value": {"operator": operator, "years": years}
            }

    # ── 3. Foot ──────────────────────────────────────────────────────────────
    for keyword, foot in FOOT_KEYWORDS.items():
        if keyword in q:
            return {"type": "foot", "value": foot}

    # ── 4. Continent ─────────────────────────────────────────────────────────
    # Multi-word aliases first (e.g. "south american" before "american")
    for alias in sorted(CONTINENT_DEMONYMS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", q):
            return {"type": "continent", "value": CONTINENT_DEMONYMS[alias]}

    # ── 5. Nationality — demonym ─────────────────────────────────────────────
    for demonym, country in DEMONYMS.items():
        if re.search(rf"\b{re.escape(demonym)}\b", q):
            return {"type": "nationality", "value": country}

    # ── 6. Nationality — country name from DB ────────────────────────────────
    has_club_or_league = any(
        w in q for w in ["club", "league", "team", "trophy", "cup", "play in", "win", "play"]
    )
    countries = db.execute(text("SELECT name FROM countries")).scalars().all()
    for country in countries:
        pattern = rf"\b(from|born|citizen|represent|represents|representing|for)\s+{re.escape(country.lower())}\b"
        if re.search(pattern, q) or (
            not has_club_or_league and re.search(rf"\b{re.escape(country.lower())}\b", q)
        ):
            return {"type": "nationality", "value": country}

    # ── 7. Competition ───────────────────────────────────────────────────────
    competitions = db.execute(text("SELECT name FROM competitions")).scalars().all()
    for comp in competitions:
        normalized_comp = comp.replace("-", " ").lower()
        if normalized_comp in q:
            return {"type": "competition", "value": comp}

    # ── 8. Club — alias lookup first ────────────────────────────────────────
    for alias, full_name in CLUB_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", q):
            is_current = any(w in q for w in ["current", "currently", "now", "today"]) \
                and not any(w in q for w in ["ever", "past", "history", "before", "did he", "has he"])
            return {"type": "current_club" if is_current else "club_history", "value": full_name}

    # ── 9. Club — full DB scan ───────────────────────────────────────────────
    clubs = db.execute(text("SELECT name FROM clubs")).scalars().all()
    for club in clubs:
        c_lower = club.lower()
        if len(c_lower) > 3 and re.search(rf"\b{re.escape(c_lower)}\b", q):
            is_current = any(w in q for w in ["current", "currently", "now", "today"]) \
                and not any(w in q for w in ["ever", "past", "history", "before", "did he", "has he"])
            return {"type": "current_club" if is_current else "club_history", "value": club}

    return None

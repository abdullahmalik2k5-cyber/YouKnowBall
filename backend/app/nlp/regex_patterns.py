import re
from sqlalchemy import text
from sqlalchemy.orm import Session

# Common country demonyms to standard country names
DEMONYMS = {
    "english": "England", "french": "France", "german": "Germany", "italian": "Italy",
    "spanish": "Spain", "brazilian": "Brazil", "argentine": "Argentina", "argentinian": "Argentina",
    "portuguese": "Portugal", "dutch": "Netherlands", "belgian": "Belgium", "croatian": "Croatia",
    "uruguayan": "Uruguay", "senegalese": "Senegal", "moroccan": "Morocco", "egyptian": "Egypt",
    "japanese": "Japan", "korean": "South Korea", "polish": "Poland", "swiss": "Switzerland",
    "swedish": "Sweden", "norwegian": "Norway", "danish": "Denmark", "austrian": "Austria",
    "turkish": "Turkey", "scottish": "Scotland", "welsh": "Wales", "irish": "Ireland",
    "algerian": "Algeria", "nigerian": "Nigeria", "ghanaian": "Ghana", "colombian": "Colombia",
    "chilean": "Chile", "mexican": "Mexico"
}

# Common football positions mapped to GK, DEF, MID, ATK
POSITIONS = {
    "goalkeeper": "GK", "gk": "GK", "keeper": "GK", "goalkeepers": "GK",
    "defender": "DEF", "def": "DEF", "centerback": "DEF", "fullback": "DEF", "defenders": "DEF",
    "midfielder": "MID", "mid": "MID", "midfielders": "MID", "winger": "ATK", "wingers": "ATK",
    "forward": "ATK", "attacker": "ATK", "attackers": "ATK", "striker": "ATK", "strikers": "ATK"
}

# Common club aliases
CLUB_ALIASES = {
    "barca": "FC Barcelona",
    "barcelona": "FC Barcelona",
    "real madrid": "Real Madrid",
    "madrid": "Real Madrid",
    "man city": "Manchester City",
    "manchester city": "Manchester City",
    "man united": "Manchester United",
    "man utd": "Manchester United",
    "manchester united": "Manchester United",
    "bayern": "Bayern Munich",
    "inter": "Inter Milan",
    "juve": "Juventus",
    "juventus": "Juventus",
    "arsenal": "Arsenal",
    "chelsea": "Chelsea",
    "liverpool": "Liverpool",
    "spurs": "Tottenham Hotspur",
    "tottenham": "Tottenham Hotspur",
    "psg": "Paris Saint-Germain"
}

def parse_with_rules(db: Session, question: str) -> dict | None:
    """Uses regex and database lookups to parse simple, common questions locally (0ms latency)."""
    q = question.lower().strip()

    # 1. Position detection
    for word, pos in POSITIONS.items():
        if re.search(rf"\b{word}\b", q):
            return {"type": "position", "value": pos}

    # 2. Demonym detection (nationality)
    for demonym, country in DEMONYMS.items():
        if re.search(rf"\b{demonym}\b", q):
            return {"type": "nationality", "value": country}

    # Country name detection from DB
    has_club_or_league = any(w in q for w in ["club", "league", "team", "trophy", "cup", "play in", "win", "play"])
    countries = db.execute(text("SELECT name FROM countries")).scalars().all()
    for country in countries:
        # Match e.g. "from Spain", "born in Spain", "represent Spain", "play for Spain"
        pattern = rf"\b(from|born|citizen|represent|represents|representing|for)\s+{country.lower()}\b"
        if re.search(pattern, q) or (not has_club_or_league and re.search(rf"\b{country.lower()}\b", q)):
            return {"type": "nationality", "value": country}

    # 3. Competition detection
    competitions = db.execute(text("SELECT name FROM competitions")).scalars().all()
    for comp in competitions:
        # Normalize competition name (replace hyphens with spaces) for matching
        normalized_comp = comp.replace("-", " ").lower()
        if normalized_comp in q:
            return {"type": "competition", "value": comp}

    # 4. Club detection via alias mapping
    for alias, full_name in CLUB_ALIASES.items():
        if re.search(rf"\b{alias}\b", q):
            # Check if user is asking about CURRENT club
            is_current = any(w in q for w in ["current", "currently", "now", "today"]) and not any(w in q for w in ["ever", "past", "history", "before", "did he"])
            type_ = "current_club" if is_current else "club_history"
            return {"type": type_, "value": full_name}

    # Club detection from DB
    clubs = db.execute(text("SELECT name FROM clubs")).scalars().all()
    for club in clubs:
        c_name = club.lower()
        # Avoid short strings matching subwords (e.g. "nice" inside "nice game")
        if len(c_name) > 3 and re.search(rf"\b{c_name}\b", q):
            is_current = any(w in q for w in ["current", "currently", "now", "today"]) and not any(w in q for w in ["ever", "past", "history", "before", "did he"])
            type_ = "current_club" if is_current else "club_history"
            return {"type": type_, "value": club}

    return None

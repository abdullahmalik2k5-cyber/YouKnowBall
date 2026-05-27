import re

# Demonym mapping to standard country name
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

COMPETITIONS = {
    "champions league": "uefa-champions-league",
    "ucl": "uefa-champions-league",
    "europa league": "europa-league",
    "uel": "europa-league",
    "premier league": "premier-league",
    "epl": "premier-league",
    "la liga": "la-liga",
    "serie a": "serie-a",
    "ligue 1": "ligue-1",
    "bundesliga": "bundesliga",
    "copa del rey": "copa-del-rey",
    "fa cup": "fa-cup",
    "efl cup": "efl-cup",
    "carabao cup": "efl-cup",
    "dfb pokal": "dfb-pokal",
    "coppa italia": "italy-cup",
    "italy cup": "italy-cup",
    "copa america": "copa-america",
    "world cup": "world-cup",
    "euros": "uefa-euro"
}

CLUBS = {
    "barca": "Futbol Club Barcelona",
    "barcelona": "Futbol Club Barcelona",
    "real madrid": "Real Madrid",
    "madrid": "Real Madrid",
    "man city": "Manchester City Football Club",
    "manchester city": "Manchester City Football Club",
    "city": "Manchester City Football Club",
    "man united": "Manchester United Football Club",
    "man utd": "Manchester United Football Club",
    "manchester united": "Manchester United Football Club",
    "united": "Manchester United Football Club",
    "bayern": "Bayern Munich",
    "bayern munich": "Bayern Munich",
    "inter": "Inter Milan",
    "inter milan": "Inter Milan",
    "juve": "Juventus",
    "juventus": "Juventus",
    "arsenal": "Arsenal",
    "chelsea": "Chelsea",
    "liverpool": "Liverpool",
    "spurs": "Tottenham Hotspur Football Club",
    "tottenham": "Tottenham Hotspur Football Club",
    "psg": "Paris Saint-Germain"
}

def normalize_entity(type_: str, value: str) -> str:
    """Normalizes raw LLM/parsed entity values to match official DB records."""
    if not value:
        return value
        
    val_clean = value.strip().lower()

    if type_ == "competition":
        # Check standard maps first
        for nickname, db_name in COMPETITIONS.items():
            if nickname in val_clean:
                return db_name
        # Fallback to kebab-casing
        return val_clean.replace(" ", "-")

    elif type_ in ["current_club", "club_history"]:
        for alias, full_name in CLUBS.items():
            if alias in val_clean:
                return full_name
        return value.strip()

    elif type_ == "nationality":
        # Check demonyms
        if val_clean in DEMONYMS:
            return DEMONYMS[val_clean]
        return value.strip().title()

    return value

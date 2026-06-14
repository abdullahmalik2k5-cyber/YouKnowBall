"""Entity normalizer.

Converts raw LLM/parsed values to canonical DB-compatible forms.
"""

# ─── Demonym → standard country name ──────────────────────────────────────────
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
    "russian": "Russia", "serbian": "Serbia", "cameroonian": "Cameroon",
    "ivorian": "Ivory Coast", "malian": "Mali", "guinean": "Guinea",
    "tunisian": "Tunisia", "american": "United States",
    "jamaican": "Jamaica", "costa rican": "Costa Rica",
}

# ─── Competition aliases → DB competition name/slug ───────────────────────────
COMPETITIONS: dict[str, str] = {
    "champions league": "uefa-champions-league",
    "ucl": "uefa-champions-league",
    "uefa champions league": "uefa-champions-league",
    "europa league": "europa-league",
    "uel": "europa-league",
    "conference league": "uefa-europa-conference-league",
    "premier league": "premier-league",
    "epl": "premier-league",
    "english premier league": "premier-league",
    "la liga": "la-liga",
    "laliga": "la-liga",
    "serie a": "serie-a",
    "italian serie a": "serie-a",
    "ligue 1": "ligue-1",
    "french ligue 1": "ligue-1",
    "bundesliga": "bundesliga",
    "german bundesliga": "bundesliga",
    "copa del rey": "copa-del-rey",
    "fa cup": "fa-cup",
    "efl cup": "efl-cup",
    "carabao cup": "efl-cup",
    "dfb pokal": "dfb-pokal",
    "dfb-pokal": "dfb-pokal",
    "coppa italia": "italy-cup",
    "italy cup": "italy-cup",
    "copa america": "copa-america",
    "world cup": "world-cup",
    "euros": "uefa-euro",
    "euro": "uefa-euro",
    "european championship": "uefa-euro",
}

# ─── Club aliases → canonical / search-friendly name ─────────────────────────
CLUBS: dict[str, str] = {
    "barca": "Futbol Club Barcelona",
    "barcelona": "Futbol Club Barcelona",
    "real madrid": "Real Madrid",
    "madrid": "Real Madrid",
    "man city": "Manchester City Football Club",
    "manchester city": "Manchester City Football Club",
    "man united": "Manchester United Football Club",
    "man utd": "Manchester United Football Club",
    "manchester united": "Manchester United Football Club",
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
    "psg": "Paris Saint-Germain",
    "paris saint-germain": "Paris Saint-Germain",
    "dortmund": "Borussia Dortmund",
    "bvb": "Borussia Dortmund",
    "atletico": "Atletico Madrid",
    "atleti": "Atletico Madrid",
}

# ─── Continent aliases → canonical continent name ─────────────────────────────
CONTINENTS: dict[str, str] = {
    "european": "Europe", "europe": "Europe",
    "african": "Africa", "africa": "Africa",
    "south american": "South America", "south america": "South America",
    "latin american": "South America", "latin": "South America",
    "north american": "North America", "north america": "North America",
    "asian": "Asia", "asia": "Asia", "middle eastern": "Asia",
    "oceanian": "Oceania", "oceania": "Oceania", "australian": "Oceania",
}


def normalize_entity(type_: str, value: str) -> str:
    """Normalises raw LLM/parsed entity values to match official DB records."""
    if not value:
        return value

    val_clean = value.strip().lower()

    if type_ == "competition":
        for nickname, db_name in COMPETITIONS.items():
            if nickname in val_clean or val_clean in nickname:
                return db_name
        # Fallback: kebab-case
        return val_clean.replace(" ", "-")

    elif type_ in ("current_club", "club_history"):
        for alias, full_name in CLUBS.items():
            if alias in val_clean:
                return full_name
        return value.strip()

    elif type_ == "nationality":
        if val_clean in DEMONYMS:
            return DEMONYMS[val_clean]
        return value.strip().title()

    elif type_ == "continent":
        return CONTINENTS.get(val_clean, value.strip().title())

    elif type_ == "foot":
        foot_map = {"left": "left", "right": "right", "both": "both"}
        return foot_map.get(val_clean, val_clean)

    # age dicts are not passed through here (handled in validator)
    return value

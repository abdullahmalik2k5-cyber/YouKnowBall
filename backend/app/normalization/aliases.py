"""Alias resolution and entity normalization."""
from typing import Dict, List

# Basic mappings for common variations
CLUB_ALIASES: Dict[str, str] = {
    "Man Utd": "Manchester United",
    "Man United": "Manchester United",
    "Spurs": "Tottenham Hotspur",
    "Tottenham": "Tottenham Hotspur",
    "Arsenal FC": "Arsenal",
    "Chelsea FC": "Chelsea",
    "PSG": "Paris Saint-Germain",
    "Barca": "FC Barcelona",
    "Barcelona": "FC Barcelona",
    "Real": "Real Madrid",
    "Juve": "Juventus FC",
    "Juventus": "Juventus FC",
    "Bayern": "Bayern Munich"
}

COUNTRY_ALIASES: Dict[str, str] = {
    "USA": "United States",
    "UK": "England", # Depending on context, usually England in football terms
    "UAE": "United Arab Emirates",
    "South Korea": "Korea, South"
}

COMPETITION_ALIASES: Dict[str, str] = {
    "Prem": "Premier League",
    "EPL": "Premier League",
    "UCL": "UEFA Champions League",
    "Champions League": "UEFA Champions League",
    "Europa": "UEFA Europa League"
}

def resolve_club(name: str) -> str:
    return CLUB_ALIASES.get(name, name)

def resolve_country(name: str) -> str:
    return COUNTRY_ALIASES.get(name, name)

def resolve_competition(name: str) -> str:
    return COMPETITION_ALIASES.get(name, name)

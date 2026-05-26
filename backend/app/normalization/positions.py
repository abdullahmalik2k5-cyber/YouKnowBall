"""Position normalization logic."""

POSITION_GROUPS = {
    "Goalkeeper": "GK",
    "Centre-Back": "DEF",
    "Left-Back": "DEF",
    "Right-Back": "DEF",
    "Defensive Midfield": "MID",
    "Central Midfield": "MID",
    "Attacking Midfield": "MID",
    "Right Midfield": "MID",
    "Left Midfield": "MID",
    "Left Winger": "ATT",
    "Right Winger": "ATT",
    "Centre-Forward": "ATT",
    "Second Striker": "ATT"
}

def normalize_position(position_name: str) -> str:
    """Map a transfermarkt position string to a broad position group."""
    if not position_name:
        return "UNKNOWN"
    return POSITION_GROUPS.get(position_name, "UNKNOWN")

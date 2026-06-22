"""Position normalization logic."""

# Maps both:
#   - Transfermarkt broad category names (e.g. "Defender", "Midfield", "Attack")
#   - Transfermarkt detailed sub-position names (e.g. "Centre-Back", "Left Winger")
# to the 4-code groups used throughout the game (GK / DEF / MID / ATK).
#
# NOTE: The raw players.csv 'position' column stores the BROAD category (e.g. "Defender"),
# while 'sub_position' stores the detail (e.g. "Centre-Back"). We must handle both
# so that normalize_position works regardless of which field is passed.
POSITION_GROUPS = {
    # ── Broad Transfermarkt categories (primary keys in players.position) ──────
    "Goalkeeper": "GK",
    "Defender": "DEF",
    "Midfield": "MID",
    "Attack": "ATK",

    # ── Detailed sub-positions (players.sub_position) ─────────────────────────
    # Goalkeepers
    "Goalkeeper": "GK",

    # Defenders
    "Centre-Back": "DEF",
    "Left-Back": "DEF",
    "Right-Back": "DEF",
    "Wing-Back": "DEF",
    "Left Wing-Back": "DEF",
    "Right Wing-Back": "DEF",

    # Midfielders
    "Defensive Midfield": "MID",
    "Central Midfield": "MID",
    "Attacking Midfield": "MID",
    "Right Midfield": "MID",
    "Left Midfield": "MID",

    # Attackers / Forwards
    "Left Winger": "ATK",
    "Right Winger": "ATK",
    "Centre-Forward": "ATK",
    "Second Striker": "ATK",
    "Striker": "ATK",
}

def normalize_position(position_name: str) -> str:
    """Map a transfermarkt position string to a broad position group (GK/DEF/MID/ATK)."""
    if not position_name:
        return "UNKNOWN"
    # Try exact match first
    result = POSITION_GROUPS.get(position_name)
    if result:
        return result
    # Case-insensitive fallback
    pos_lower = position_name.strip().lower()
    for key, val in POSITION_GROUPS.items():
        if key.lower() == pos_lower:
            return val
    return "UNKNOWN"

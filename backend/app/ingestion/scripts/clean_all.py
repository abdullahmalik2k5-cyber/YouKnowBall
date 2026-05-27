"""Clean raw data from Transfermarkt and prepare it for database insertion with high-performance filtering."""
import os
import pandas as pd
import uuid
from app.ingestion.scripts.utils import generate_uuid
from app.normalization.positions import normalize_position

# Paths
BASE_DIR = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE_DIR, "..", "raw", "transfermarkt")
CLEANED_DIR = os.path.join(BASE_DIR, "..", "cleaned")

os.makedirs(CLEANED_DIR, exist_ok=True)

# Shared memory sets for high-speed raw filtering before UUID generation
VALID_RAW_COUNTRIES = set()
VALID_RAW_COMPETITIONS = set()
VALID_RAW_CLUBS = set()
VALID_RAW_PLAYERS = set()
VALID_RAW_GAMES = set()

# Final UUID sets for database referential integrity
VALID_COUNTRIES = set()
VALID_COMPETITIONS = set()
VALID_CLUBS = set()
VALID_PLAYERS = set()
VALID_GAMES = set()

def load_raw(filename: str) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(path):
        print(f"Warning: {filename} not found.")
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

def save_cleaned(df: pd.DataFrame, filename: str):
    if df.empty:
        return
    path = os.path.join(CLEANED_DIR, filename)
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows to {filename}")

def to_nullable_int(df, col_name, default=None):
    """Safely convert a column to pandas Nullable Integer (Int64)."""
    if col_name not in df.columns:
        return pd.Series([default] * len(df), dtype=pd.Int64Dtype())
    return pd.to_numeric(df[col_name], errors='coerce').astype(pd.Int64Dtype())

def clean_countries():
    print("Cleaning countries...")
    df = load_raw("countries.csv")
    if df.empty: return
    
    global VALID_RAW_COUNTRIES
    VALID_RAW_COUNTRIES = set(df['country_id'].dropna().astype(int).tolist())
    
    df['id'] = df['country_id'].apply(lambda x: generate_uuid('country', x))
    df = df.rename(columns={'country_name': 'name'})
    
    cols = ['id', 'name', 'country_code', 'confederation']
    df_clean = df[cols].dropna(subset=['id']).drop_duplicates(subset=['id'])
    
    global VALID_COUNTRIES
    VALID_COUNTRIES = set(df_clean['id'].tolist())
    save_cleaned(df_clean, "countries.csv")

def clean_competitions():
    print("Cleaning competitions...")
    df = load_raw("competitions.csv")
    if df.empty: return
    
    global VALID_RAW_COMPETITIONS
    VALID_RAW_COMPETITIONS = set(df['competition_id'].dropna().tolist()) # Competitions have string IDs in Transfermarkt (e.g. 'GB1')
    
    df['id'] = df['competition_id'].apply(lambda x: generate_uuid('competition', x))
    cols = ['id', 'name', 'type', 'sub_type', 'country_name', 'confederation', 'domestic_league_code']
    df_clean = df[cols].dropna(subset=['id']).drop_duplicates(subset=['id'])
    
    global VALID_COMPETITIONS
    VALID_COMPETITIONS = set(df_clean['id'].tolist())
    save_cleaned(df_clean, "competitions.csv")

def clean_clubs():
    print("Cleaning clubs...")
    df = load_raw("clubs.csv")
    if df.empty: return
    
    global VALID_RAW_CLUBS
    VALID_RAW_CLUBS = set(df['club_id'].dropna().astype(int).tolist())
    
    df['id'] = df['club_id'].apply(lambda x: generate_uuid('club', x))
    
    df['domestic_competition_id'] = df['domestic_competition_id'].apply(
        lambda x: generate_uuid('competition', x) if pd.notnull(x) else None
    )
    if 'country_id' in df.columns:
        df['country_id'] = df['country_id'].apply(
            lambda x: generate_uuid('country', x) if pd.notnull(x) else None
        )
    else:
        df['country_id'] = None
        
    df['stadium_seats'] = to_nullable_int(df, 'stadium_seats')
    
    cols = ['id', 'name', 'domestic_competition_id', 'country_id', 'stadium_name', 'stadium_seats']
    for col in cols:
        if col not in df.columns:
            df[col] = None
            
    df_clean = df[cols].dropna(subset=['id']).drop_duplicates(subset=['id'])
    
    # Enforce FK constraints
    df_clean.loc[~df_clean['domestic_competition_id'].isin(VALID_COMPETITIONS), 'domestic_competition_id'] = None
    df_clean.loc[~df_clean['country_id'].isin(VALID_COUNTRIES), 'country_id'] = None
    
    global VALID_CLUBS
    VALID_CLUBS = set(df_clean['id'].tolist())
    save_cleaned(df_clean, "clubs.csv")

def clean_players():
    print("Cleaning players (filtering to last_season >= 2016)...")
    df = load_raw("players.csv")
    if df.empty: return
    
    # High-speed pre-filtering: only keep players active since 2021
    df = df[df['last_season'] >= 2021]
    
    global VALID_RAW_PLAYERS
    VALID_RAW_PLAYERS = set(df['player_id'].dropna().astype(int).tolist())
    
    df['id'] = df['player_id'].apply(lambda x: generate_uuid('player', x))
    df['current_club_id'] = df['current_club_id'].apply(
        lambda x: generate_uuid('club', x) if pd.notnull(x) else None
    )
    
    # Attempt to resolve nationality_id using country name mapping
    countries_df = pd.read_csv(os.path.join(CLEANED_DIR, "countries.csv"))
    country_name_to_id = dict(zip(countries_df['name'].str.lower(), countries_df['id']))
    df['nationality_id'] = df['country_of_citizenship'].str.lower().map(country_name_to_id)
    
    df = df.rename(columns={
        'foot': 'preferred_foot',
        'height_in_cm': 'height_cm',
        'market_value_in_eur': 'market_value_eur'
    })
    
    # Compute age dynamically if not present
    if 'age' not in df.columns and 'date_of_birth' in df.columns:
        dob = pd.to_datetime(df['date_of_birth'], errors='coerce')
        today = pd.to_datetime('today')
        df['age'] = (today.year - dob.dt.year) - ((today.month < dob.dt.month) | ((today.month == dob.dt.month) & (today.day < dob.dt.day))).astype(int)
        
    df['age'] = to_nullable_int(df, 'age')
    df['height_cm'] = to_nullable_int(df, 'height_cm')
    df['market_value_eur'] = to_nullable_int(df, 'market_value_eur')
    df['international_caps'] = to_nullable_int(df, 'international_caps', default=0)
    df['international_goals'] = to_nullable_int(df, 'international_goals', default=0)
    
    df['active'] = df['last_season'] >= 2021
    df['position_group'] = df['position'].apply(normalize_position)
    
    cols = ['id', 'name', 'date_of_birth', 'age', 'nationality_id', 'position', 'sub_position', 
            'position_group', 'preferred_foot', 'height_cm', 'current_club_id', 'market_value_eur', 
            'international_caps', 'international_goals', 'active']
            
    for col in cols:
        if col not in df.columns:
            df[col] = None
            
    df_clean = df[cols].dropna(subset=['id']).drop_duplicates(subset=['id'])
    
    # Enforce FK constraints
    df_clean.loc[~df_clean['current_club_id'].isin(VALID_CLUBS), 'current_club_id'] = None
    df_clean.loc[~df_clean['nationality_id'].isin(VALID_COUNTRIES), 'nationality_id'] = None
    
    global VALID_PLAYERS
    VALID_PLAYERS = set(df_clean['id'].tolist())
    save_cleaned(df_clean, "players.csv")

def clean_national_teams():
    print("Cleaning national teams...")
    df = load_raw("national_teams.csv")
    if df.empty: return
    
    df['id'] = df['national_team_id'].apply(lambda x: generate_uuid('national_team', x))
    if 'country_id' in df.columns:
        df['country_id'] = df['country_id'].apply(
            lambda x: generate_uuid('country', x) if pd.notnull(x) else None
        )
    else:
        df['country_id'] = None
        
    df['fifa_ranking'] = to_nullable_int(df, 'fifa_ranking')
    df['squad_size'] = to_nullable_int(df, 'squad_size')
    
    cols = ['id', 'name', 'country_id', 'fifa_ranking', 'squad_size', 'average_age']
    for col in cols:
        if col not in df.columns:
            df[col] = None
            
    df_clean = df[cols].dropna(subset=['id']).drop_duplicates(subset=['id'])
    df_clean.loc[~df_clean['country_id'].isin(VALID_COUNTRIES), 'country_id'] = None
    save_cleaned(df_clean, "national_teams.csv")

def clean_games():
    print("Cleaning games (filtering to season >= 2016)...")
    df = load_raw("games.csv")
    if df.empty: return
    
    # Strictly filter by season to meet 500MB free database storage limit!
    df = df[df['season'] >= 2021]
    
    global VALID_RAW_GAMES
    VALID_RAW_GAMES = set(df['game_id'].dropna().astype(int).tolist())
    
    df['id'] = df['game_id'].apply(lambda x: generate_uuid('game', x))
    df['competition_id'] = df['competition_id'].apply(
        lambda x: generate_uuid('competition', x) if pd.notnull(x) else None
    )
    df['home_club_id'] = df['home_club_id'].apply(
        lambda x: generate_uuid('club', x) if pd.notnull(x) else None
    )
    df['away_club_id'] = df['away_club_id'].apply(
        lambda x: generate_uuid('club', x) if pd.notnull(x) else None
    )
    
    df = df.rename(columns={'home_club_goals': 'home_goals', 'away_club_goals': 'away_goals'})
    
    df['season'] = to_nullable_int(df, 'season')
    df['home_goals'] = to_nullable_int(df, 'home_goals')
    df['away_goals'] = to_nullable_int(df, 'away_goals')
    
    cols = ['id', 'competition_id', 'season', 'date', 'home_club_id', 'away_club_id', 'home_goals', 'away_goals']
    for col in cols:
        if col not in df.columns:
            df[col] = None
            
    df_clean = df[cols].dropna(subset=['id']).drop_duplicates(subset=['id'])
    
    # Enforce FK constraints
    df_clean.loc[~df_clean['competition_id'].isin(VALID_COMPETITIONS), 'competition_id'] = None
    df_clean.loc[~df_clean['home_club_id'].isin(VALID_CLUBS), 'home_club_id'] = None
    df_clean.loc[~df_clean['away_club_id'].isin(VALID_CLUBS), 'away_club_id'] = None
    
    global VALID_GAMES
    VALID_GAMES = set(df_clean['id'].tolist())
    save_cleaned(df_clean, "games.csv")

def clean_appearances():
    print("Cleaning appearances (high-speed filtering)...")
    df = load_raw("appearances.csv")
    if df.empty: return
    
    # High-speed pre-filtering on raw IDs
    df = df[df['game_id'].isin(VALID_RAW_GAMES) & df['player_id'].isin(VALID_RAW_PLAYERS)]
    if df.empty: return
    
    df['id'] = df['appearance_id'].apply(
        lambda x: generate_uuid('appearance', x) if pd.notnull(x) else str(uuid.uuid4())
    )
    df['game_id'] = df['game_id'].apply(lambda x: generate_uuid('game', x) if pd.notnull(x) else None)
    df['player_id'] = df['player_id'].apply(lambda x: generate_uuid('player', x) if pd.notnull(x) else None)
    df['club_id'] = df['player_club_id'].apply(lambda x: generate_uuid('club', x) if pd.notnull(x) else None)
    if 'competition_id' in df.columns:
        df['competition_id'] = df['competition_id'].apply(
            lambda x: generate_uuid('competition', x) if pd.notnull(x) else None
        )
    
    df['minutes_played'] = to_nullable_int(df, 'minutes_played', default=0)
    df['goals'] = to_nullable_int(df, 'goals', default=0)
    df['assists'] = to_nullable_int(df, 'assists', default=0)
    df['yellow_cards'] = to_nullable_int(df, 'yellow_cards', default=0)
    df['red_cards'] = to_nullable_int(df, 'red_cards', default=0)
    
    cols = ['id', 'game_id', 'player_id', 'club_id', 'date', 'minutes_played', 'goals', 'assists', 'yellow_cards', 'red_cards', 'competition_id']
    for col in cols:
        if col not in df.columns:
            df[col] = None
            
    df_clean = df[cols].dropna(subset=['game_id', 'player_id']).drop_duplicates(subset=['id'])
    
    # Filter strictly to validated UUIDs
    df_clean = df_clean[df_clean['game_id'].isin(VALID_GAMES) & df_clean['player_id'].isin(VALID_PLAYERS)]
    df_clean.loc[~df_clean['club_id'].isin(VALID_CLUBS), 'club_id'] = None
    df_clean.loc[~df_clean['competition_id'].isin(VALID_COMPETITIONS), 'competition_id'] = None
    
    save_cleaned(df_clean, "appearances.csv")

def clean_game_lineups():
    print("Cleaning game lineups (high-speed filtering)...")
    df = load_raw("game_lineups.csv")
    if df.empty: return
    
    # High-speed pre-filtering on raw IDs
    df = df[df['game_id'].isin(VALID_RAW_GAMES) & df['player_id'].isin(VALID_RAW_PLAYERS)]
    if df.empty: return
    
    df['id'] = df['game_lineups_id'].apply(
        lambda x: generate_uuid('game_lineup', x) if pd.notnull(x) else str(uuid.uuid4())
    )
    df['game_id'] = df['game_id'].apply(lambda x: generate_uuid('game', x) if pd.notnull(x) else None)
    df['player_id'] = df['player_id'].apply(lambda x: generate_uuid('player', x) if pd.notnull(x) else None)
    df['club_id'] = df['club_id'].apply(lambda x: generate_uuid('club', x) if pd.notnull(x) else None)
    
    df['is_starting'] = df['type'] == 'starting_lineup'
    df['is_captain'] = df['team_captain'] == 1 if 'team_captain' in df.columns else False
    
    cols = ['id', 'game_id', 'player_id', 'club_id', 'position', 'is_starting', 'is_captain']
    for col in cols:
        if col not in df.columns:
            df[col] = None
            
    df_clean = df[cols].dropna(subset=['game_id', 'player_id']).drop_duplicates(subset=['id'])
    
    # Filter strictly to validated UUIDs (including club_id which is NOT NULL in database)
    df_clean = df_clean[
        df_clean['game_id'].isin(VALID_GAMES) & 
        df_clean['player_id'].isin(VALID_PLAYERS) & 
        df_clean['club_id'].isin(VALID_CLUBS)
    ]
    
    save_cleaned(df_clean, "game_lineups.csv")

def clean_game_events():
    print("Cleaning game events (high-speed filtering)...")
    df = load_raw("game_events.csv")
    if df.empty: return
    
    # High-speed pre-filtering on raw IDs
    df = df[df['game_id'].isin(VALID_RAW_GAMES)]
    if df.empty: return
    
    df['id'] = df['game_event_id'].apply(
        lambda x: generate_uuid('game_event', x) if pd.notnull(x) else str(uuid.uuid4())
    )
    df['game_id'] = df['game_id'].apply(lambda x: generate_uuid('game', x) if pd.notnull(x) else None)
    df['player_id'] = df['player_id'].apply(lambda x: generate_uuid('player', x) if pd.notnull(x) else None)
    if 'player_assist_id' in df.columns:
        df['assist_player_id'] = df['player_assist_id'].apply(
            lambda x: generate_uuid('player', x) if pd.notnull(x) else None
        )
    else:
        df['assist_player_id'] = None
        
    df['minute'] = to_nullable_int(df, 'minute')
    
    cols = ['id', 'game_id', 'player_id', 'type', 'minute', 'description', 'assist_player_id']
    for col in cols:
        if col not in df.columns:
            df[col] = None
            
    df_clean = df[cols].dropna(subset=['game_id']).drop_duplicates(subset=['id'])
    
    # Filter strictly to validated UUIDs
    df_clean = df_clean[df_clean['game_id'].isin(VALID_GAMES)]
    df_clean.loc[~df_clean['player_id'].isin(VALID_PLAYERS), 'player_id'] = None
    df_clean.loc[~df_clean['assist_player_id'].isin(VALID_PLAYERS), 'assist_player_id'] = None
    
    save_cleaned(df_clean, "game_events.csv")

def clean_club_games():
    print("Cleaning club games (high-speed filtering)...")
    df = load_raw("club_games.csv")
    if df.empty: return
    
    # High-speed pre-filtering on raw IDs
    df = df[df['game_id'].isin(VALID_RAW_GAMES) & df['club_id'].isin(VALID_RAW_CLUBS)]
    if df.empty: return
    
    df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    df['game_id'] = df['game_id'].apply(lambda x: generate_uuid('game', x) if pd.notnull(x) else None)
    df['club_id'] = df['club_id'].apply(lambda x: generate_uuid('club', x) if pd.notnull(x) else None)
    df['opponent_id'] = df['opponent_id'].apply(lambda x: generate_uuid('club', x) if pd.notnull(x) else None)
    
    df['is_home'] = df['hosting'] == 'Home' if 'hosting' in df.columns else False
    df['is_win'] = df['is_win'] == 1 if 'is_win' in df.columns else False
    
    cols = ['id', 'game_id', 'club_id', 'opponent_id', 'is_home', 'is_win']
    for col in cols:
        if col not in df.columns:
            df[col] = None
            
    df_clean = df[cols].dropna(subset=['game_id', 'club_id']).drop_duplicates(subset=['id'])
    
    # Filter strictly to validated UUIDs
    df_clean = df_clean[df_clean['game_id'].isin(VALID_GAMES) & df_clean['club_id'].isin(VALID_CLUBS)]
    df_clean.loc[~df_clean['opponent_id'].isin(VALID_CLUBS), 'opponent_id'] = None
    
    save_cleaned(df_clean, "club_games.csv")

def clean_player_valuations():
    print("Cleaning player valuations (high-speed filtering)...")
    df = load_raw("player_valuations.csv")
    if df.empty: return
    
    # High-speed pre-filtering on raw IDs
    df = df[df['player_id'].isin(VALID_RAW_PLAYERS)]
    if df.empty: return
    
    df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    df['player_id'] = df['player_id'].apply(lambda x: generate_uuid('player', x) if pd.notnull(x) else None)
    df['club_id'] = df['current_club_id'].apply(
        lambda x: generate_uuid('club', x) if pd.notnull(x) else None
    )
    df['market_value_eur'] = to_nullable_int(df, 'market_value_in_eur')
    
    cols = ['id', 'player_id', 'date', 'market_value_eur', 'club_id']
    for col in cols:
        if col not in df.columns:
            df[col] = None
            
    df_clean = df[cols].dropna(subset=['player_id']).drop_duplicates(subset=['id'])
    
    # Filter strictly to validated UUIDs
    df_clean = df_clean[df_clean['player_id'].isin(VALID_PLAYERS)]
    df_clean.loc[~df_clean['club_id'].isin(VALID_CLUBS), 'club_id'] = None
    
    save_cleaned(df_clean, "player_valuations.csv")

def clean_transfers_and_history():
    print("Cleaning transfers and history (high-speed filtering)...")
    df = load_raw("transfers.csv")
    if df.empty: return
    
    # High-speed pre-filtering on raw IDs
    df = df[df['player_id'].isin(VALID_RAW_PLAYERS)]
    if df.empty: return
    
    df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    df['player_id'] = df['player_id'].apply(lambda x: generate_uuid('player', x))
    
    def safe_club_uuid(x):
        try:
            return generate_uuid('club', int(x)) if pd.notnull(x) else None
        except:
            return None
            
    df['from_club_id'] = df['from_club_id'].apply(safe_club_uuid)
    df['to_club_id'] = df['to_club_id'].apply(safe_club_uuid)
    
    df['transfer_fee'] = to_nullable_int(df, 'transfer_fee')
    df['market_value_eur'] = to_nullable_int(df, 'market_value_in_eur')
    
    t_cols = ['id', 'player_id', 'from_club_id', 'to_club_id', 'transfer_date', 'transfer_fee', 'market_value_eur']
    for col in t_cols:
        if col not in df.columns:
            df[col] = None
            
    transfers_clean = df[t_cols].dropna(subset=['player_id']).drop_duplicates(subset=['id'])
    
    # Filter strictly to validated UUIDs
    transfers_clean = transfers_clean[transfers_clean['player_id'].isin(VALID_PLAYERS)]
    transfers_clean.loc[~transfers_clean['from_club_id'].isin(VALID_CLUBS), 'from_club_id'] = None
    transfers_clean.loc[~transfers_clean['to_club_id'].isin(VALID_CLUBS), 'to_club_id'] = None
    
    save_cleaned(transfers_clean, "transfers.csv")

    history = pd.DataFrame()
    history['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    history['player_id'] = df['player_id']
    history['club_id'] = df['to_club_id']
    history['start_date'] = df['transfer_date']
    history['end_date'] = None
    history['transfer_season'] = df['transfer_season'] if 'transfer_season' in df.columns else None
    
    history_clean = history.dropna(subset=['club_id', 'player_id']).drop_duplicates(subset=['id'])
    
    # Filter strictly to validated UUIDs
    history_clean = history_clean[history_clean['player_id'].isin(VALID_PLAYERS) & history_clean['club_id'].isin(VALID_CLUBS)]
    
    save_cleaned(history_clean, "player_club_history.csv")

if __name__ == "__main__":
    print("Starting optimized data cleaning pipeline...")
    clean_countries()
    clean_competitions()
    clean_clubs()
    clean_players()
    clean_national_teams()
    clean_transfers_and_history()
    clean_games()
    clean_appearances()
    clean_game_lineups()
    clean_game_events()
    clean_club_games()
    clean_player_valuations()
    print("Pipeline completed successfully.")

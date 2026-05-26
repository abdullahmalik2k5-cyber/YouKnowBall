"""Clean all raw data from Transfermarkt and prepare it for database insertion."""
import os
import pandas as pd
from app.ingestion.scripts.utils import generate_uuid

# Paths
BASE_DIR = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE_DIR, "..", "raw", "transfermarkt")
CLEANED_DIR = os.path.join(BASE_DIR, "..", "cleaned")

# Ensure cleaned directory exists
os.makedirs(CLEANED_DIR, exist_ok=True)

def load_raw(filename: str) -> pd.DataFrame:
    """Load a raw CSV file."""
    path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(path):
        print(f"Warning: {filename} not found.")
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

def save_cleaned(df: pd.DataFrame, filename: str):
    """Save a cleaned DataFrame to CSV."""
    if df.empty:
        return
    path = os.path.join(CLEANED_DIR, filename)
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows to {filename}")

def clean_countries():
    """Clean countries data."""
    print("Cleaning countries...")
    df = load_raw("countries.csv")
    if df.empty: return
    
    # Map to schema: id, name, country_code, confederation
    df['id'] = df['country_id'].apply(lambda x: generate_uuid('country', x))
    df = df.rename(columns={
        'country_name': 'name'
    })
    
    # Keep only necessary columns
    cols = ['id', 'name', 'country_code', 'confederation']
    save_cleaned(df[cols].dropna(subset=['id']), "countries.csv")

def clean_competitions():
    """Clean competitions data."""
    print("Cleaning competitions...")
    df = load_raw("competitions.csv")
    if df.empty: return
    
    df['id'] = df['competition_id'].apply(lambda x: generate_uuid('competition', x))
    
    cols = ['id', 'name', 'type', 'sub_type', 'country_name', 'confederation', 'domestic_league_code']
    save_cleaned(df[cols].dropna(subset=['id']), "competitions.csv")

def clean_clubs():
    """Clean clubs data."""
    print("Cleaning clubs...")
    df = load_raw("clubs.csv")
    if df.empty: return
    
    df['id'] = df['club_id'].apply(lambda x: generate_uuid('club', x))
    df['domestic_competition_id'] = df['domestic_competition_id'].apply(lambda x: generate_uuid('competition', x))
    # We need country_id which isn't directly in clubs.csv? Wait, clubs.csv usually doesn't have country_id, but it has competition which links to country. 
    # Let's map country_id if it exists, otherwise leave empty.
    # The models say: domestic_competition_id, country_id, stadium_name, stadium_seats
    if 'country_id' in df.columns:
        df['country_id'] = df['country_id'].apply(lambda x: generate_uuid('country', x))
    else:
        df['country_id'] = None
        
    cols = ['id', 'name', 'domestic_competition_id', 'country_id', 'stadium_name', 'stadium_seats']
    
    # Ensure columns exist
    for col in cols:
        if col not in df.columns:
            df[col] = None
            
    save_cleaned(df[cols].dropna(subset=['id']), "clubs.csv")

def clean_players():
    """Clean players data."""
    print("Cleaning players...")
    df = load_raw("players.csv")
    if df.empty: return
    
    df['id'] = df['player_id'].apply(lambda x: generate_uuid('player', x))
    df['current_club_id'] = df['current_club_id'].apply(lambda x: generate_uuid('club', x))
    # We don't have direct nationality_id (country_id). We have 'country_of_citizenship'. 
    # To map country_of_citizenship to country UUID, we'd need a lookup. 
    # For now, leave nationality_id empty, or we can map it if we load countries.
    df['nationality_id'] = None 
    
    df = df.rename(columns={
        'sub_position': 'sub_position',
        'foot': 'preferred_foot',
        'height_in_cm': 'height_cm',
        'market_value_in_eur': 'market_value_eur'
    })
    
    df['active'] = True # Default assumption
    df['international_caps'] = df.get('international_caps', 0)
    df['international_goals'] = df.get('international_goals', 0)
    
    cols = ['id', 'name', 'date_of_birth', 'nationality_id', 'position', 'sub_position', 
            'preferred_foot', 'height_cm', 'current_club_id', 'market_value_eur', 
            'international_caps', 'international_goals', 'active']
            
    # Ensure columns exist
    for col in cols:
        if col not in df.columns:
            df[col] = None
            
    save_cleaned(df[cols].dropna(subset=['id']), "players.csv")

import uuid

def clean_national_teams():
    print("Cleaning national teams...")
    df = load_raw("national_teams.csv")
    if df.empty: return
    
    df['id'] = df['national_team_id'].apply(lambda x: generate_uuid('national_team', x))
    if 'country_id' in df.columns:
        df['country_id'] = df['country_id'].apply(lambda x: generate_uuid('country', x))
    else:
        df['country_id'] = None
        
    cols = ['id', 'name', 'country_id', 'fifa_ranking', 'squad_size', 'average_age']
    for col in cols:
        if col not in df.columns:
            df[col] = None
    save_cleaned(df[cols].dropna(subset=['id']), "national_teams.csv")

def clean_transfers_and_history():
    print("Cleaning transfers and history...")
    df = load_raw("transfers.csv")
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
    
    transfers = df.rename(columns={'market_value_in_eur': 'market_value_eur'})
    t_cols = ['id', 'player_id', 'from_club_id', 'to_club_id', 'transfer_date', 'transfer_fee', 'market_value_eur']
    for col in t_cols:
        if col not in transfers.columns:
            transfers[col] = None
    save_cleaned(transfers[t_cols], "transfers.csv")

    history = pd.DataFrame()
    history['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    history['player_id'] = df['player_id']
    history['club_id'] = df['to_club_id']
    history['start_date'] = df['transfer_date']
    history['end_date'] = None
    history['transfer_season'] = df['transfer_season'] if 'transfer_season' in df.columns else None
    
    history = history.dropna(subset=['club_id'])
    save_cleaned(history, "player_club_history.csv")

def clean_games():
    print("Cleaning games...")
    df = load_raw("games.csv")
    if df.empty: return
    
    df['id'] = df['game_id'].apply(lambda x: generate_uuid('game', x))
    df['competition_id'] = df['competition_id'].apply(lambda x: generate_uuid('competition', x) if pd.notnull(x) else None)
    df['home_club_id'] = df['home_club_id'].apply(lambda x: generate_uuid('club', x) if pd.notnull(x) else None)
    df['away_club_id'] = df['away_club_id'].apply(lambda x: generate_uuid('club', x) if pd.notnull(x) else None)
    
    df = df.rename(columns={'home_club_goals': 'home_goals', 'away_club_goals': 'away_goals'})
    
    cols = ['id', 'competition_id', 'season', 'date', 'home_club_id', 'away_club_id', 'home_goals', 'away_goals']
    for col in cols:
        if col not in df.columns:
            df[col] = None
    save_cleaned(df[cols].dropna(subset=['id']), "games.csv")

def clean_appearances():
    print("Cleaning appearances...")
    df = load_raw("appearances.csv")
    if df.empty: return
    
    df['id'] = df['appearance_id'].apply(lambda x: generate_uuid('appearance', x) if pd.notnull(x) else str(uuid.uuid4()))
    df['game_id'] = df['game_id'].apply(lambda x: generate_uuid('game', x) if pd.notnull(x) else None)
    df['player_id'] = df['player_id'].apply(lambda x: generate_uuid('player', x) if pd.notnull(x) else None)
    df['club_id'] = df['player_club_id'].apply(lambda x: generate_uuid('club', x) if pd.notnull(x) else None)
    if 'competition_id' in df.columns:
        df['competition_id'] = df['competition_id'].apply(lambda x: generate_uuid('competition', x) if pd.notnull(x) else None)
    
    cols = ['id', 'game_id', 'player_id', 'club_id', 'date', 'minutes_played', 'goals', 'assists', 'yellow_cards', 'red_cards', 'competition_id']
    for col in cols:
        if col not in df.columns:
            df[col] = 0 if col in ['minutes_played', 'goals', 'assists', 'yellow_cards', 'red_cards'] else None
    
    save_cleaned(df[cols].dropna(subset=['game_id', 'player_id']), "appearances.csv")

def clean_game_lineups():
    print("Cleaning game lineups...")
    df = load_raw("game_lineups.csv")
    if df.empty: return
    
    df['id'] = df['game_lineups_id'].apply(lambda x: generate_uuid('game_lineup', x) if pd.notnull(x) else str(uuid.uuid4()))
    df['game_id'] = df['game_id'].apply(lambda x: generate_uuid('game', x) if pd.notnull(x) else None)
    df['player_id'] = df['player_id'].apply(lambda x: generate_uuid('player', x) if pd.notnull(x) else None)
    df['club_id'] = df['club_id'].apply(lambda x: generate_uuid('club', x) if pd.notnull(x) else None)
    
    df['is_starting'] = df['type'] == 'starting_lineup'
    df['is_captain'] = df['team_captain'] == 1 if 'team_captain' in df.columns else False
    
    cols = ['id', 'game_id', 'player_id', 'club_id', 'position', 'is_starting', 'is_captain']
    for col in cols:
        if col not in df.columns:
            df[col] = None
    save_cleaned(df[cols].dropna(subset=['game_id', 'player_id']), "game_lineups.csv")

def clean_game_events():
    print("Cleaning game events...")
    df = load_raw("game_events.csv")
    if df.empty: return
    
    df['id'] = df['game_event_id'].apply(lambda x: generate_uuid('game_event', x) if pd.notnull(x) else str(uuid.uuid4()))
    df['game_id'] = df['game_id'].apply(lambda x: generate_uuid('game', x) if pd.notnull(x) else None)
    df['player_id'] = df['player_id'].apply(lambda x: generate_uuid('player', x) if pd.notnull(x) else None)
    if 'player_assist_id' in df.columns:
        df['assist_player_id'] = df['player_assist_id'].apply(lambda x: generate_uuid('player', x) if pd.notnull(x) else None)
    else:
        df['assist_player_id'] = None
        
    cols = ['id', 'game_id', 'player_id', 'type', 'minute', 'description', 'assist_player_id']
    for col in cols:
        if col not in df.columns:
            df[col] = None
    save_cleaned(df[cols].dropna(subset=['game_id']), "game_events.csv")

def clean_club_games():
    print("Cleaning club games...")
    df = load_raw("club_games.csv")
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
    save_cleaned(df[cols].dropna(subset=['game_id', 'club_id']), "club_games.csv")

def clean_player_valuations():
    print("Cleaning player valuations...")
    df = load_raw("player_valuations.csv")
    if df.empty: return
    
    df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
    df['player_id'] = df['player_id'].apply(lambda x: generate_uuid('player', x) if pd.notnull(x) else None)
    
    cols = ['id', 'player_id']
    save_cleaned(df[cols].dropna(subset=['player_id']), "player_valuations.csv")

if __name__ == "__main__":
    print("Starting data cleaning pipeline...")
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
    print("Pipeline completed.")

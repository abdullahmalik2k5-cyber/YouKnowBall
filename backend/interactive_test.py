import sys
import os
from sqlalchemy import text

# Add backend directory to sys path so we can import app
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from verify_database import _load_env
_load_env()

from app.db.database import SessionLocal
from app.nlp.parser import parse_question
from app.game.queries import handlers
from app.game.candidate_engine.engine import CandidateEngine

def log_and_execute(db, query_str, params):
    """Prints the exact SQL query and params before executing."""
    print("\n" + "="*50)
    print("🔥 [DATABASE LOG] Executing SQL Query:")
    print(query_str.strip())
    print(f"👉 [PARAMETERS]: {params}")
    print("="*50)
    
    result = db.execute(text(query_str), params)
    return result

def main():
    db = SessionLocal()
    
    # Fix the hidden player to Erling Haaland
    haaland_id = "66da82cb-d561-5f56-8b71-ef716f1c4322"
    
    # Verify player exists
    player_exists = db.execute(
        text("SELECT name FROM players WHERE id = :id"), 
        {"id": haaland_id}
    ).fetchone()
    
    if not player_exists:
        print("Error: Erling Haaland was not found in the database. Please run ingestion first.")
        return
        
    print("\n⚽ =============================================== ⚽")
    print("      YOU KNOW BALL? - TERMINAL INTERACTIVE TESTER")
    print("             (Target Player: Erling Haaland)")
    print("⚽ =============================================== ⚽")
    
    engine = CandidateEngine(db)
    print(f"\nInitial Candidate Pool Size: {engine.get_remaining_count()} active players\n")
    
    while True:
        try:
            question = input("Ask a question about the player (or 'q' to quit) > ").strip()
            if not question:
                continue
            if question.lower() == 'q':
                print("Exiting game. Thanks for playing!")
                break
                
            # 1. Parse using NLP engine
            print("\n🤖 [NLP Parsing] Analyzing your question...")
            parsed = parse_question(db, question)
            print(f"👉 [NLP Result]: Type='{parsed['type']}', Value='{parsed['value']}'")
            
            if parsed["type"] == "invalid" or not parsed["value"]:
                print("❌ [NLP Output] The parser could not understand your question. Try asking about his nationality, current club, past clubs, position, or competition.")
                continue
                
            # 2. Run Database Query
            answer = "UNKNOWN"
            sql_query = ""
            params = {}
            fact_details = ""
            
            if parsed["type"] == "nationality":
                sql_query = """
                    SELECT c.name
                    FROM players p
                    JOIN countries c ON p.nationality_id = c.id
                    WHERE p.id = :pid
                """
                params = {"pid": haaland_id}
                res = log_and_execute(db, sql_query, params).scalar()
                if res:
                    answer = "YES" if parsed["value"].lower() in res.lower() or res.lower() in parsed["value"].lower() else "NO"
                    fact_details = f"His nationality is {res}."
                engine.filter_by_nationality(parsed["value"], answer)
                
            elif parsed["type"] == "current_club":
                sql_query = """
                    SELECT c.name
                    FROM players p
                    JOIN clubs c ON p.current_club_id = c.id
                    WHERE p.id = :pid
                """
                params = {"pid": haaland_id}
                res = log_and_execute(db, sql_query, params).scalar()
                if res:
                    answer = "YES" if parsed["value"].lower() in res.lower() or res.lower() in parsed["value"].lower() else "NO"
                    fact_details = f"His current club is {res}."
                engine.filter_by_current_club(parsed["value"], answer)
                
            elif parsed["type"] == "club_history":
                sql_query = """
                    SELECT COUNT(*)
                    FROM player_club_history pch
                    JOIN clubs c ON pch.club_id = c.id
                    WHERE pch.player_id = :pid AND LOWER(c.name) LIKE :club
                """
                params = {"pid": haaland_id, "club": f"%{parsed['value'].lower()}%"}
                res = log_and_execute(db, sql_query, params).scalar()
                answer = "YES" if res > 0 else "NO"
                
                # Fetch all past clubs for rich explainer facts
                clubs_res = db.execute(
                    text("SELECT DISTINCT c.name FROM player_club_history pch JOIN clubs c ON pch.club_id = c.id WHERE pch.player_id = :pid"),
                    {"pid": haaland_id}
                ).scalars().all()
                fact_details = f"He has played for: {', '.join(clubs_res)}."
                engine.filter_by_club_history(parsed["value"], answer)
                
            elif parsed["type"] == "position":
                sql_query = """
                    SELECT position_group
                    FROM players
                    WHERE id = :pid
                """
                params = {"pid": haaland_id}
                res = log_and_execute(db, sql_query, params).scalar()
                if res:
                    answer = "YES" if res.lower() == parsed["value"].lower() else "NO"
                    pos_map = {"GK": "Goalkeeper", "DEF": "Defender", "MID": "Midfielder", "ATK": "Attacker"}
                    fact_details = f"His position group is {pos_map.get(res, res)}."
                engine.filter_by_position(parsed["value"], answer)
                
            elif parsed["type"] == "competition":
                sql_query = """
                    SELECT COUNT(*)
                    FROM appearances a
                    JOIN competitions c ON a.competition_id = c.id
                    WHERE a.player_id = :pid AND LOWER(c.name) LIKE :comp
                """
                params = {"pid": haaland_id, "comp": f"%{parsed['value'].lower()}%"}
                res = log_and_execute(db, sql_query, params).scalar()
                answer = "YES" if res > 0 else "NO"
                
                # Fetch all competition names for rich explainer facts
                comps_res = db.execute(
                    text("SELECT DISTINCT c.name FROM appearances a JOIN competitions c ON a.competition_id = c.id WHERE a.player_id = :pid"),
                    {"pid": haaland_id}
                ).scalars().all()
                fact_details = f"He has played in: {', '.join([c.replace('-', ' ').title() for c in comps_res])}."
                engine.filter_by_competition_history(parsed["value"], answer)
            
            # Generate and print the AI Explainer conversational response
            from app.nlp.llm.explainer import generate_explanation
            explanation = generate_explanation(question, answer, "Erling Haaland", fact_details)
            print(f"\n💬 [AI Host]: \"{explanation}\"")
            print(f"🎯 [DATABASE ANSWER]: {answer}")
            print(f"👥 [Remaining Candidates]: {engine.get_remaining_count()}")
            
            if engine.get_remaining_count() == 1:
                winner_id = list(engine.pool)[0]
                winner_name = db.execute(text("SELECT name FROM players WHERE id = :id"), {"id": winner_id}).scalar()
                print(f"\n🏆 WINNER! The engine narrowed it down to: {winner_name}")
                break
            elif engine.get_remaining_count() == 0:
                print("\n⚠️ No players match this criteria in your database pool!")
                break
                
            print("-" * 50 + "\n")
        except KeyboardInterrupt:
            print("\nExiting game...")
            break

if __name__ == "__main__":
    main()

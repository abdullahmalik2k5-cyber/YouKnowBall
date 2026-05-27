import sys
import os
import re
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
    """Executes a parameterized SQL query silently (or logging it if debug is needed)."""
    return db.execute(text(query_str), params)

def main():
    db = SessionLocal()
    
    # 1. Randomly pick an active player who has a club and nationality
    print("🔄 Picking a random hidden player from database...")
    pick_query = """
        SELECT p.id, p.name
        FROM players p
        JOIN clubs c ON p.current_club_id = c.id
        JOIN countries nat ON p.nationality_id = nat.id
        WHERE p.active = true
        ORDER BY RANDOM()
        LIMIT 1
    """
    player = db.execute(text(pick_query)).fetchone()
    if not player:
        print("❌ Error: No active players found in the database. Please run ingestion first.")
        return
        
    hidden_player_id = str(player[0])
    hidden_player_name = str(player[1])
    
    print("\n⚽ =============================================== ⚽")
    print("                  YOU KNOW BALL? - PLAY")
    print("                (A Hidden Player is Set!)")
    print("⚽ =============================================== ⚽")
    print("Rules:")
    print("- You have up to 20 questions to narrow down the player.")
    print("- You have exactly 3 guesses to name the player.")
    print("- Type 'g' or 'guess' to submit a guess at any time.")
    print("- Type 'q' to quit.")
    print("====================================================\n")
    
    engine = CandidateEngine(db)
    print(f"Initial Candidate Pool Size: {engine.get_remaining_count()} active players\n")
    
    question_count = 0
    max_questions = 20
    guess_count = 0
    max_guesses = 3
    
    while True:
        try:
            # Check game limits
            if question_count >= max_questions:
                print(f"\n⚠️ Game Over: You have reached the maximum of {max_questions} questions!")
                print(f"The hidden player was: {hidden_player_name}")
                break
                
            status_line = f"[Q: {question_count}/{max_questions} | Guesses: {guess_count}/{max_guesses}]"
            action = input(f"{status_line} Enter question (or 'g' to guess, 'q' to quit) > ").strip()
            
            if not action:
                continue
            
            if action.lower() == 'q':
                print(f"Exiting game. The hidden player was: {hidden_player_name}")
                break
                
            # Submit a guess
            if action.lower() in ['g', 'guess']:
                guess_count += 1
                player_guess = input(f"🤔 Submit your player guess ({guess_count}/{max_guesses}) > ").strip()
                
                # Check match (case insensitive, allow minor space variations)
                normalized_guess = re.sub(r'\s+', ' ', player_guess.strip().lower())
                normalized_target = hidden_player_name.lower()
                
                # Check if full guess or last name matches
                if normalized_guess == normalized_target or normalized_guess in normalized_target:
                    print(f"\n🏆 CONGRATULATIONS! You guessed it right! It is indeed {hidden_player_name}!")
                    break
                else:
                    print(f"❌ Incorrect Guess! That is not the hidden player.")
                    if guess_count >= max_guesses:
                        print(f"\n💀 Game Over: You used all {max_guesses} guesses!")
                        print(f"The hidden player was: {hidden_player_name}")
                        break
                    continue
            
            # Otherwise, parse and execute the question
            question = action
            question_count += 1
            
            print("\n🤖 [NLP Parsing] Analyzing your question...")
            parsed = parse_question(db, question)
            
            if parsed["type"] == "invalid" or not parsed["value"]:
                err_msg = parsed.get("message", "The parser could not understand your question. Try asking about nationality, club history, current club, position, or competition.")
                print(f"❌ [NLP Output] {err_msg}")
                question_count -= 1 # Don't charge a question turn for invalid parsing
                continue
                
            print(f"👉 [NLP Result]: Type='{parsed['type']}', Value='{parsed['value']}'")
            
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
                params = {"pid": hidden_player_id}
                res = db.execute(text(sql_query), params).scalar()
                if res:
                    answer = "YES" if parsed["value"].lower() in res.lower() or res.lower() in parsed["value"].lower() else "NO"
                    if answer == "YES":
                        fact_details = f"His nationality is {res}."
                    else:
                        fact_details = f"His nationality is not {parsed['value']}."
                engine.filter_by_nationality(parsed["value"], answer)
                
            elif parsed["type"] == "current_club":
                sql_query = """
                    SELECT c.name
                    FROM players p
                    JOIN clubs c ON p.current_club_id = c.id
                    WHERE p.id = :pid
                """
                params = {"pid": hidden_player_id}
                res = db.execute(text(sql_query), params).scalar()
                if res:
                    answer = "YES" if parsed["value"].lower() in res.lower() or res.lower() in parsed["value"].lower() else "NO"
                    if answer == "YES":
                        fact_details = f"His current club is {res}."
                    else:
                        fact_details = f"His current club is not {parsed['value']}."
                engine.filter_by_current_club(parsed["value"], answer)
                
            elif parsed["type"] == "club_history":
                sql_query = """
                    SELECT COUNT(*)
                    FROM player_club_history pch
                    JOIN clubs c ON pch.club_id = c.id
                    WHERE pch.player_id = :pid AND LOWER(c.name) LIKE :club
                """
                params = {"pid": hidden_player_id, "club": f"%{parsed['value'].lower()}%"}
                res = db.execute(text(sql_query), params).scalar()
                answer = "YES" if res > 0 else "NO"
                if answer == "YES":
                    fact_details = f"He has played for {parsed['value']} in his career."
                else:
                    fact_details = f"He has never played for {parsed['value']}."
                engine.filter_by_club_history(parsed["value"], answer)
                
            elif parsed["type"] == "position":
                sql_query = """
                    SELECT position_group
                    FROM players
                    WHERE id = :pid
                """
                params = {"pid": hidden_player_id}
                res = db.execute(text(sql_query), params).scalar()
                if res:
                    answer = "YES" if res.lower() == parsed["value"].lower() else "NO"
                    pos_map = {"GK": "Goalkeeper", "DEF": "Defender", "MID": "Midfielder", "ATK": "Attacker"}
                    asked_pos = pos_map.get(parsed["value"].upper(), parsed["value"])
                    if answer == "YES":
                        fact_details = f"His position is {asked_pos}."
                    else:
                        fact_details = f"His position is not {asked_pos}."
                engine.filter_by_position(parsed["value"], answer)
                
            elif parsed["type"] == "competition":
                sql_query = """
                    SELECT COUNT(*)
                    FROM appearances a
                    JOIN competitions c ON a.competition_id = c.id
                    WHERE a.player_id = :pid AND LOWER(c.name) LIKE :comp
                """
                params = {"pid": hidden_player_id, "comp": f"%{parsed['value'].lower()}%"}
                res = db.execute(text(sql_query), params).scalar()
                answer = "YES" if res > 0 else "NO"
                if answer == "YES":
                    fact_details = f"He has played in the {parsed['value']}."
                else:
                    fact_details = f"He has never played in the {parsed['value']}."
                engine.filter_by_competition_history(parsed["value"], answer)
            
            # Generate explanation - name is passed to generate_explanation to censor it if LLM leaks it
            from app.nlp.llm.explainer import generate_explanation
            explanation = generate_explanation(question, answer, hidden_player_name, fact_details)
            print(f"\n💬 [AI Host]: \"{explanation}\"")
            print(f"🎯 [DATABASE ANSWER]: {answer}")
            print(f"👥 [Remaining Candidates]: {engine.get_remaining_count()}")
            print("-" * 50 + "\n")
            
        except KeyboardInterrupt:
            print(f"\nExiting game. The hidden player was: {hidden_player_name}")
            break

if __name__ == "__main__":
    main()

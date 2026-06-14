import sys, os

sys.path.insert(0, os.path.abspath('backend'))
os.chdir('backend')

# Load env
with open('../.env', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip().strip('"\'')

results = []

try:
    from app.nlp.regex_patterns import parse_with_rules, POSITIONS, CONTINENT_DEMONYMS, FOOT_KEYWORDS, AGE_PATTERNS
    results.append('regex_patterns.py: OK')
except Exception as e:
    results.append(f'regex_patterns.py: FAIL — {e}')

try:
    from app.nlp.normalizer import normalize_entity
    results.append('normalizer.py: OK')
except Exception as e:
    results.append(f'normalizer.py: FAIL — {e}')

try:
    from app.nlp.llm.validators import validate_llm_json, ParsedQuestion
    results.append('validators.py: OK')
except Exception as e:
    results.append(f'validators.py: FAIL — {e}')

try:
    from app.nlp.llm.prompts import SYSTEM_PROMPT, get_user_prompt
    results.append('prompts.py: OK')
except Exception as e:
    results.append(f'prompts.py: FAIL — {e}')

try:
    from app.nlp.llm.explainer import generate_explanation
    results.append('explainer.py: OK')
except Exception as e:
    results.append(f'explainer.py: FAIL — {e}')

try:
    from app.game.difficulty import get_player_pool_ids, select_hidden_player
    results.append('difficulty.py: OK')
except Exception as e:
    results.append(f'difficulty.py: FAIL — {e}')

try:
    from app.game.candidate_engine.engine import CandidateEngine, COUNTRY_TO_CONTINENT
    results.append('engine.py: OK')
except Exception as e:
    results.append(f'engine.py: FAIL — {e}')

try:
    from app.game.queries.handlers import (
        handle_nationality, handle_current_club, handle_club_history,
        handle_position, handle_competition_history,
        handle_continent, handle_age, handle_foot
    )
    results.append('handlers.py: OK')
except Exception as e:
    results.append(f'handlers.py: FAIL — {e}')

print()
for r in results:
    print(r)

# Quick unit tests for new parsers
print()
print("=== Quick NLP Rule Tests ===")
try:
    # Test continent detection
    r = parse_with_rules(None, "Is he European?")
    print(f"'Is he European?' => {r}")
    
    r = parse_with_rules(None, "Is he South American?")
    print(f"'Is he South American?' => {r}")
    
    r = parse_with_rules(None, "Is he African?")
    print(f"'Is he African?' => {r}")

    # Test age detection
    r = parse_with_rules(None, "Is he under 30?")
    print(f"'Is he under 30?' => {r}")
    
    r = parse_with_rules(None, "Is he older than 28?")
    print(f"'Is he older than 28?' => {r}")

    # Test foot detection
    r = parse_with_rules(None, "Is he left-footed?")
    print(f"'Is he left-footed?' => {r}")
    
    r = parse_with_rules(None, "Does he prefer his right foot?")
    print(f"'Does he prefer his right foot?' => {r}")

    # Test position
    r = parse_with_rules(None, "Is he a striker?")
    print(f"'Is he a striker?' => {r}")

    # Test nationality demonym
    r = parse_with_rules(None, "Is he Brazilian?")
    print(f"'Is he Brazilian?' => {r}")
    
except Exception as e:
    print(f"Rule parser test error: {e}")

# Test validators
print()
print("=== Validator Tests ===")
try:
    # Test continent
    r = validate_llm_json('{"type": "continent", "value": "Europe"}')
    print(f"continent Europe => {r}")
    
    # Test age
    r = validate_llm_json('{"type": "age", "value": {"operator": "lt", "years": 30}}')
    print(f"age lt 30 => {r}")
    
    # Test foot
    r = validate_llm_json('{"type": "foot", "value": "left"}')
    print(f"foot left => {r}")
    
    # Test that bad type is rejected
    r = validate_llm_json('{"type": "bad_type", "value": "whatever"}')
    print(f"invalid type => {r} (should be None)")

except Exception as e:
    print(f"Validator test error: {e}")

print()
print("=== All checks done ===")

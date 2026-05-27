import json
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

class ParsedQuestion(BaseModel):
    type: Literal["nationality", "current_club", "club_history", "position", "competition", "invalid"]
    value: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        return v

    @field_validator("value")
    @classmethod
    def validate_value(cls, v, info):
        # If type is position, value must be GK, DEF, MID, or ATK
        if info.data.get("type") == "position":
            if v:
                pos = v.upper()
                if pos in ["GK", "DEF", "MID", "ATK"]:
                    return pos
                # Handle mapping common full names
                pos_map = {
                    "GOALKEEPER": "GK",
                    "DEFENDER": "DEF",
                    "MIDFIELDER": "MID",
                    "ATTACKER": "ATK",
                    "STRIKER": "ATK",
                    "FORWARD": "ATK",
                    "WINGER": "ATK"
                }
                if pos in pos_map:
                    return pos_map[pos]
            return "MID" # Default fallback
        return v

from app.nlp.normalizer import normalize_entity

def validate_llm_json(raw_response: str) -> Optional[dict]:
    """Cleans up markdown JSON blocks and validates against the schema."""
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        # Strip code fences if present
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    
    try:
        data = json.loads(cleaned)
        parsed = ParsedQuestion(**data)
        res = parsed.model_dump()
        if res.get("value"):
            res["value"] = normalize_entity(res["type"], res["value"])
        return res
    except Exception:
        return None

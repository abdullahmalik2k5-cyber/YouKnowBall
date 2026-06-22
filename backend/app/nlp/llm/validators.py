import json
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional, Union


# ─── Age value schema ─────────────────────────────────────────────────────────

class AgeValue(BaseModel):
    operator: Literal["lt", "lte", "gt", "gte", "eq"]
    years: int

    @field_validator("years")
    @classmethod
    def validate_years(cls, v):
        if not (10 <= v <= 60):
            raise ValueError(f"Age {v} is out of plausible football range (10–60).")
        return v


# ─── Main parsed question schema ──────────────────────────────────────────────

class ParsedQuestion(BaseModel):
    type: Literal[
        "nationality", "current_club", "club_history", "position",
        "competition", "continent", "age", "foot", "big_six", "invalid"
    ]
    value: Optional[Union[str, dict]] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        return v

    @model_validator(mode="after")
    def validate_value_for_type(self):
        t = self.type
        v = self.value

        if t == "invalid":
            self.value = None
            return self

        if t == "big_six":
            self.value = "big_six"
            return self

        if t == "position":
            if v:
                pos = str(v).upper()
                pos_map = {
                    "GOALKEEPER": "GK", "KEEPER": "GK", "GOALIE": "GK",
                    "DEFENDER": "DEF", "BACK": "DEF",
                    "MIDFIELDER": "MID", "MIDFIELD": "MID",
                    "ATTACKER": "ATK", "STRIKER": "ATK", "FORWARD": "ATK",
                    "WINGER": "ATK",
                }
                if pos in ["GK", "DEF", "MID", "ATK"]:
                    self.value = pos
                elif pos in pos_map:
                    self.value = pos_map[pos]
                else:
                    self.value = "MID"  # safe fallback
            else:
                self.value = "MID"

        elif t == "continent":
            valid_continents = {"Europe", "South America", "Africa", "Asia", "North America", "Oceania"}
            if v not in valid_continents:
                # Try to normalise
                v_lower = str(v).lower() if v else ""
                continent_map = {
                    "europe": "Europe", "european": "Europe",
                    "africa": "Africa", "african": "Africa",
                    "south america": "South America", "south american": "South America",
                    "latin america": "South America",
                    "north america": "North America", "north american": "North America",
                    "asia": "Asia", "asian": "Asia",
                    "oceania": "Oceania", "oceanian": "Oceania",
                }
                self.value = continent_map.get(v_lower, v)

        elif t == "age":
            if isinstance(v, dict):
                # Validate the nested AgeValue schema
                age_obj = AgeValue(**v)
                self.value = {"operator": age_obj.operator, "years": age_obj.years}
            elif v is None:
                raise ValueError("Age type requires a value with operator and years.")

        elif t == "foot":
            if v:
                foot_lower = str(v).lower()
                foot_map = {
                    "left": "left", "right": "right", "both": "both",
                    "two-footed": "both", "ambidextrous": "both",
                }
                self.value = foot_map.get(foot_lower, foot_lower)

        return self


# ─── Import normalizer (placed here to avoid circular imports at module level) ─

from app.nlp.normalizer import normalize_entity


def validate_llm_json(raw_response: str) -> Optional[dict]:
    """Cleans up markdown JSON blocks and validates against the schema."""
    cleaned = raw_response.strip()
    # Strip surrounding quotes if LLM wrapped the JSON in quotes
    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1]
    # Strip code fences if present
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        lines = lines[:-1] if lines and lines[-1].startswith("```") else lines
        cleaned = "\n".join(lines).strip()

    try:
        data = json.loads(cleaned)
        parsed = ParsedQuestion(**data)
        res = parsed.model_dump()
        # Normalise string values (not age dicts)
        if res.get("value") and isinstance(res["value"], str):
            res["value"] = normalize_entity(res["type"], res["value"])
        return res
    except Exception:
        return None

"""Utility functions for data ingestion pipeline."""
import uuid

# Define a custom namespace for Transfermarkt deterministic UUID generation
NAMESPACE_TM = uuid.uuid5(uuid.NAMESPACE_OID, "transfermarkt")

def generate_uuid(entity_type: str, tm_id: str | int) -> str | None:
    """
    Generate a deterministic UUID from a Transfermarkt ID.
    
    Args:
        entity_type: Type of the entity (e.g., 'player', 'club', 'competition').
        tm_id: The Transfermarkt identifier (string or integer).
        
    Returns:
        String representation of the UUID, or None if tm_id is null/empty.
    """
    if tm_id is None or tm_id == '' or str(tm_id).lower() in ['nan', 'nat']:
        return None
        
    # Combine entity type and id for uniqueness across types (e.g., player_123 vs club_123)
    unique_string = f"{entity_type}_{tm_id}"
    return str(uuid.uuid5(NAMESPACE_TM, unique_string))

"""Regenerate packages/contracts/episode.schema.json from the Pydantic models."""

from newsroom_core.contracts import EPISODE_SCHEMA_PATH, episode_schema_json

EPISODE_SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
EPISODE_SCHEMA_PATH.write_text(episode_schema_json())
print(f"wrote {EPISODE_SCHEMA_PATH}")

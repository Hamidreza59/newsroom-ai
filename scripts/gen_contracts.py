"""Regenerate the JSON Schemas in packages/contracts from the Pydantic models."""

from newsroom_core.contracts import (
    EPISODE_SCHEMA_PATH,
    SITE_SCHEMA_PATH,
    episode_schema_json,
    site_schema_json,
)

EPISODE_SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
for path, content in ((EPISODE_SCHEMA_PATH, episode_schema_json()),
                      (SITE_SCHEMA_PATH, site_schema_json())):
    path.write_text(content)
    print(f"wrote {path}")

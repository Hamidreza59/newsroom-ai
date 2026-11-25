from __future__ import annotations

import json

from newsroom_core.config import ROOT
from newsroom_core.models import Episode

EPISODE_SCHEMA_PATH = ROOT / "packages" / "contracts" / "episode.schema.json"


def _strip_titles(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "properties":
                for prop in value.values():
                    prop.pop("title", None)
            _strip_titles(value)
    elif isinstance(node, list):
        for item in node:
            _strip_titles(item)


def episode_schema_json() -> str:
    """JSON Schema of the episode contract, as written to packages/contracts."""
    schema = Episode.model_json_schema(by_alias=True, mode="serialization")
    _strip_titles(schema)
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"

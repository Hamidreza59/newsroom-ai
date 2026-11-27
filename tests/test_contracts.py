from newsroom_core.contracts import (
    EPISODE_SCHEMA_PATH,
    SITE_SCHEMA_PATH,
    episode_schema_json,
    site_schema_json,
)

HINT = "run `make contracts` to regenerate packages/contracts and the studio types"


def test_episode_schema_matches_committed_file():
    assert EPISODE_SCHEMA_PATH.read_text() == episode_schema_json(), HINT


def test_site_schema_matches_committed_file():
    assert SITE_SCHEMA_PATH.read_text() == site_schema_json(), HINT

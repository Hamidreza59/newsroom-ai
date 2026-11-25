from newsroom_core.contracts import EPISODE_SCHEMA_PATH, episode_schema_json


def test_episode_schema_matches_committed_file():
    assert EPISODE_SCHEMA_PATH.read_text() == episode_schema_json(), (
        "run `make contracts` to regenerate packages/contracts and the studio types")

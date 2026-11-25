from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

from newsroom_core.config import Settings
from newsroom_core.models import ShowPackage, ShowScript

from newsroom_voice.producer import Producer, TooLong
from newsroom_voice.tts import download_kokoro, make_tts

log = logging.getLogger("newsroom_voice.cli")


def _today() -> date:
    return datetime.now(ZoneInfo("America/New_York")).date()


def shorten(script: ShowScript) -> ShowScript:
    """Deterministic time budget, same priority as the agents: quiz recap, explainer, stories, quiz."""
    if len(script.stories) > 3:
        return script.model_copy(update={"stories": script.stories[:-1]})
    if script.quiz and script.quiz.reveal_lines:
        return script.model_copy(update={"quiz": script.quiz.model_copy(
            update={"reveal_lines": [], "reveal": ""})})
    if script.explainer:
        return script.model_copy(update={"explainer": None})
    if len(script.stories) > 2:
        return script.model_copy(update={"stories": script.stories[:-1]})
    if script.quiz:
        return script.model_copy(update={"quiz": None})
    raise ValueError("nothing left to cut")


def cmd_build(args: argparse.Namespace) -> None:
    settings = Settings()
    if args.tts:
        settings.tts_provider = args.tts
    show_date = date.fromisoformat(args.date) if args.date else _today()
    out_dir = settings.episode_dir(show_date.isoformat())
    path = out_dir / "package.json"
    if not path.exists():
        sys.exit(f"{path} not found; run `newsroom-agents run` first")
    pkg = ShowPackage.model_validate_json(path.read_text())
    if not pkg.approved:
        sys.exit(f"{path} is not approved (needs_review={pkg.needs_review}); review script.md "
                 "and re-run the agents with approval before building the episode")

    producer = Producer(settings, make_tts(settings))
    script = pkg.script
    while True:
        try:
            episode = producer.build(script, pkg.snapshot, show_date)
            break
        except TooLong as exc:
            log.info("%s; over %.0fs, cutting", exc, settings.max_seconds)
            try:
                script = shorten(script)
            except ValueError:
                sys.exit(f"{exc}: nothing left to cut")
    producer.write(episode, out_dir)
    log.info("episode ready: %s (%.1fs, tts=%s)", out_dir,
             episode.duration_in_frames / episode.fps, producer.tts.name)


def cmd_setup(_: argparse.Namespace) -> None:
    settings = Settings()
    download_kokoro(settings.models_dir)
    print(f"Kokoro voice models ready in {settings.models_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="newsroom-voice", description="Narration and timing")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="turn package.json into episode.json and narration")
    build.add_argument("--date", help="show date YYYY-MM-DD (default: today, US/Eastern)")
    build.add_argument("--tts", choices=["kokoro", "say", "silent"])
    build.set_defaults(func=cmd_build)
    sub.add_parser("setup", help="download the free Kokoro voice models").set_defaults(
        func=cmd_setup)

    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(name)-22s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("phonemizer").setLevel(logging.ERROR)
    args.func(args)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from newsroom_core.config import Settings

log = logging.getLogger("newsroom_publisher")

_CHAPTER = re.compile(r"^(\d+:\d{2}) (.+)$")
_SOURCE = re.compile(r"^• (.+) \((.+)\): (\S+)$")


def _today() -> date:
    return datetime.now(ZoneInfo("America/New_York")).date()


def _read(path: Path) -> dict:
    return json.loads(path.read_text())


def _chapters(description: str) -> list[dict]:
    found = (_CHAPTER.match(line) for line in description.splitlines())
    return [{"time": m.group(1), "title": m.group(2)} for m in found if m]


def _sources(episode_dir: Path, description: str) -> list[dict]:
    package = episode_dir / "package.json"
    if package.exists():
        stories = _read(package)["script"]["stories"]
        return [{"title": s["headline"], "publisher": s["source"], "url": s["url"]}
                for s in stories]
    found = (_SOURCE.match(line) for line in description.splitlines())
    return [{"title": m.group(1), "publisher": m.group(2), "url": m.group(3)} for m in found if m]


def _quiz(episode: dict, episode_dir: Path) -> dict | None:
    scene = next((s for s in episode["scenes"] if s["type"] == "quiz"), None)
    if not scene:
        return None
    quiz = {"question": scene["headline"], "options": scene["options"], "reveal": scene["reveal"]}
    package = episode_dir / "package.json"
    if package.exists():
        script_quiz = _read(package)["script"].get("quiz")
        if script_quiz:
            quiz["answer"] = script_quiz["options"][script_quiz["answer_index"]]
    return quiz


def _media(episode_dir: Path, name: str) -> str | None:
    return f"../{name}" if (episode_dir / name).exists() else None


def build_post(episode_dir: Path) -> dict:
    episode = _read(episode_dir / "episode.json")
    youtube = _read(episode_dir / "youtube.json")
    scenes = episode["scenes"]
    market = next((s["headline"] for s in scenes if s["type"] == "market"), "")
    stories = [s["headline"] for s in scenes if s["type"] == "news"]
    summary = f"Markets: {market}. Top stories: " + "; ".join(stories) + "." if stories else market
    return {
        "title": youtube["title"],
        "date": episode["date"],
        "show": episode["showName"],
        "summary": summary,
        "sources": _sources(episode_dir, youtube["description"]),
        "chapters": _chapters(youtube["description"]),
        "quiz": _quiz(episode, episode_dir),
        "tags": youtube["tags"],
        "disclaimer": episode["disclaimer"],
        "video": _media(episode_dir, "video.mp4"),
        "short": _media(episode_dir, "short.mp4"),
        "thumbnail": _media(episode_dir, "thumbnail.png"),
    }


def render_markdown(post: dict) -> str:
    md = [f"# {post['title']}", "", f"*{post['show']} — {post['date']}*", "", post["summary"], ""]
    if post["video"]:
        md += [f"[Watch the episode]({post['video']})", ""]
    if post["chapters"]:
        md += ["## Chapters", *(f"- {c['time']} {c['title']}" for c in post["chapters"]), ""]
    if post["sources"]:
        md += ["## Sources",
               *(f"- [{s['title']}]({s['url']}) ({s['publisher']})" for s in post["sources"]), ""]
    quiz = post["quiz"]
    if quiz:
        md += ["## Daily quiz", quiz["question"], *(f"- {o}" for o in quiz["options"])]
        if quiz.get("answer"):
            md.append(f"\nAnswer: {quiz['answer']}")
        md.append("")
    md += [f"*{post['disclaimer']}*", "", "Tags: " + ", ".join(post["tags"]), ""]
    return "\n".join(md)


def update_feed(out_dir: Path, post: dict) -> Path:
    feed_path = out_dir / "web" / "index.json"
    feed = _read(feed_path) if feed_path.exists() else []
    day = post["date"]

    def rel(name: str | None) -> str | None:
        return f"../{day}/{name}" if name else None

    entry = {
        "date": day, "title": post["title"], "summary": post["summary"],
        "post": f"../{day}/web/post.json", "article": f"../{day}/web/post.md",
        "video": rel(post["video"] and "video.mp4"), "short": rel(post["short"] and "short.mp4"),
        "thumbnail": rel(post["thumbnail"] and "thumbnail.png"),
    }
    feed = sorted([e for e in feed if e["date"] != day] + [entry], key=lambda e: e["date"],
                  reverse=True)
    feed_path.parent.mkdir(parents=True, exist_ok=True)
    feed_path.write_text(json.dumps(feed, indent=2, ensure_ascii=False))
    return feed_path


def cmd_build(args: argparse.Namespace) -> None:
    settings = Settings()
    show_date = date.fromisoformat(args.date) if args.date else _today()
    episode_dir = settings.episode_dir(show_date.isoformat())
    for name in ("episode.json", "youtube.json"):
        if not (episode_dir / name).exists():
            sys.exit(f"{episode_dir / name} not found; run `newsroom-voice build` first")
    post = build_post(episode_dir)
    web = episode_dir / "web"
    web.mkdir(exist_ok=True)
    (web / "post.json").write_text(json.dumps(post, indent=2, ensure_ascii=False))
    (web / "post.md").write_text(render_markdown(post))
    feed = update_feed(settings.out_dir, post)
    log.info("post ready: %s (feed: %s)", web, feed)


def main() -> None:
    parser = argparse.ArgumentParser(prog="newsroom-publisher", description="Website posts")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="write the website post and update the feed")
    build.add_argument("--date", help="show date YYYY-MM-DD (default: today, US/Eastern)")
    build.set_defaults(func=cmd_build)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)-22s %(message)s",
                        datefmt="%H:%M:%S")
    args.func(args)


if __name__ == "__main__":
    main()

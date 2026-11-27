from __future__ import annotations

import hashlib
import html
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import feedparser
from newsroom_core.models import NewsItem
from newsroom_core.net import http_client
from newsroom_core.text import tokens

log = logging.getLogger(__name__)

RSS_FEEDS: list[tuple[str, str]] = [
    ("The Verge", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("MIT Technology Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
    ("Wired", "https://www.wired.com/feed/tag/ai/latest/rss"),
    ("Engadget", "https://www.engadget.com/rss.xml"),
    ("STAT", "https://www.statnews.com/feed/"),
    ("BioPharma Dive", "https://www.biopharmadive.com/feeds/news/"),
    ("MIT Technology Review", "https://www.technologyreview.com/topic/biotechnology/feed"),
    ("Nature Biotechnology", "https://www.nature.com/nbt.rss"),
    ("GEN", "https://www.genengnews.com/feed/"),
    ("Labiotech", "https://www.labiotech.eu/feed/"),
]
FINANCE_FEEDS: list[tuple[str, str, bool]] = [
    ("CNBC", "https://www.cnbc.com/id/100003114/device/rss/rss.html", False),
    ("CNBC", "https://www.cnbc.com/id/10000664/device/rss/rss.html", True),
    ("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories", True),
    ("Finextra", "https://www.finextra.com/rss/headlines.aspx", True),
]
SOURCE_WEIGHT = {"CNBC": 1.1, "MarketWatch": 1.0, "Finextra": 0.9, "MIT Technology Review": 1.2, "Ars Technica": 1.1, "The Verge": 1.1, "Wired": 1.0,
                 "STAT": 1.2, "Nature Biotechnology": 1.2,
                 "BioPharma Dive": 1.1, "GEN": 1.0, "Labiotech": 0.9}
CATEGORY_WEIGHT = {"AI": 1.5, "Biotech": 1.4, "Tech": 1.0}
HN_SEARCH = "https://hn.algolia.com/api/v1/search_by_date"

AI_PATTERN = re.compile(
    r"\b(ai|a\.i\.|artificial intelligence|llm|gpt|chatgpt|openai|anthropic|claude|gemini|"
    r"deepmind|mistral|llama|machine learning|neural|chatbot|agentic|agents?|copilot|nvidia|"
    r"model|inference|robot\w*|transformer)\b",
    re.IGNORECASE,
)
TECH_PATTERN = re.compile(
    r"\b(chip|semiconductor|apple|google|microsoft|amazon|meta|tesla|startup|software|cloud|"
    r"cyber\w*|hack\w*|quantum|smartphone|iphone|android|data center|browser|app|tech\w*)\b",
    re.IGNORECASE,
)
BIO_PATTERN = re.compile(
    r"\b(biotech\w*|protein\w*|gene|genes|genetic\w*|genom\w*|crispr|gene editing|mrna|vaccine\w*|"
    r"antibod\w*|clinical trials?|fda|drug\w*|therap\w*|oncology|cancer|biolog\w*|enzyme\w*|"
    r"peptide\w*|alphafold|cell therapy|pharma\w*|molecule\w*|biomedical|dna|rna|microbiome)\b",
    re.IGNORECASE,
)
STRICT_AI_PATTERN = re.compile(
    r"\b(ai|a\.i\.|artificial intelligence|llm|gpt|chatgpt|openai|anthropic|claude|gemini|"
    r"deepmind|machine learning|chatbot|agentic|ai agents?|copilot|nvidia)\b",
    re.IGNORECASE,
)
FINANCE_PATTERN = re.compile(
    r"\b(stocks?|shares|earnings|ipo|interest rates?|bonds?|treasur(?:y|ies)|inflation|"
    r"wall street|s&p|nasdaq|dow|banks?|banking|trading|traders?|hedge funds?|investors?|"
    r"fintech|payments?|crypto\w*|bitcoin|lending|insurers?|insurance|asset managers?|"
    r"private equity|valuation|dividends?|rally|selloff|rate cuts?|market cap|etfs?)\b",
    re.IGNORECASE,
)
FINANCE_CASED = re.compile(r"\b(Fed|FOMC|IPO|S&P|SEC|ECB)\b")
TAG_RE = re.compile(r"<[^>]+>")
PAYWALL_PREFIX = re.compile(r"^(?:STAT\+|Exclusive|Premium|Subscriber[s]?(?: only)?)\s*:\s*", re.IGNORECASE)


def item_id(url: str) -> str:
    return hashlib.sha1(url.split("?")[0].encode()).hexdigest()[:12]


def clean(text: str, limit: int = 500) -> str:
    text = html.unescape(TAG_RE.sub(" ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return PAYWALL_PREFIX.sub("", text)[:limit]


def categorize(text: str) -> str | None:
    if BIO_PATTERN.search(text):
        return "Biotech"
    if AI_PATTERN.search(text):
        return "AI"
    if TECH_PATTERN.search(text):
        return "Tech"
    return None


def compute_tags(text: str, default_markets: bool = False,
                 category: str | None = None) -> list[str]:
    strict_ai = bool(STRICT_AI_PATTERN.search(text))
    ai = strict_ai or category == "AI"
    finance = default_markets or bool(FINANCE_PATTERN.search(text) or FINANCE_CASED.search(text))
    tags = []
    if ai:
        tags.append("ai")
    if TECH_PATTERN.search(text) or category == "Tech":
        tags.append("tech")
    if BIO_PATTERN.search(text) or category == "Biotech":
        tags.append("biotech")
    if finance:
        tags.append("markets")
    if strict_ai and finance:
        tags.append("ai-finance")
    return tags


def is_video_item(item: NewsItem) -> bool:
    """Stories for the daily show: anything tagged AI, tech or biotech."""
    return bool({"ai", "tech", "biotech"} & set(item.tags))


def fetch_rss(source: str, url: str, since: datetime, default_markets: bool = False,
              finance_feed: bool = False) -> list[NewsItem]:
    with http_client() as client:
        resp = client.get(url)
        resp.raise_for_status()
    feed = feedparser.parse(resp.text)
    items = []
    for entry in feed.entries:
        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if not parsed:
            continue
        published = datetime.fromtimestamp(time.mktime(parsed), UTC)
        if published < since:
            continue
        title = clean(entry.get("title", ""), 200)
        summary = clean(entry.get("summary", ""))
        text = f"{title} {summary}"
        category = categorize(text)
        tags = compute_tags(text, default_markets, category)
        if not title or not (category or (finance_feed and tags)):
            continue
        hours_old = (datetime.now(UTC) - published).total_seconds() / 3600
        items.append(
            NewsItem(
                id=item_id(entry.link),
                title=title,
                url=entry.link,
                source=source,
                published=published.isoformat(),
                summary=summary,
                category=category or "Tech",
                tags=tags,
                from_feed=True,
                score=SOURCE_WEIGHT.get(source, 0.9) * CATEGORY_WEIGHT.get(category or "", 1.0)
                * max(0.3, 1 - hours_old / 48),
            )
        )
    return items


MULTI_PART_TLDS = {"co.uk", "com.au", "co.jp", "com.br"}


def source_from_domain(domain: str) -> str:
    parts = domain.lower().removeprefix("www.").split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in MULTI_PART_TLDS:
        parts = parts[:-1]
    label = parts[-2] if len(parts) >= 2 else parts[0]
    if len(label) <= 2:
        return domain.lower().removeprefix("www.")
    return label if len(label) <= 3 else label.capitalize()


def fetch_hacker_news(since: datetime, min_points: int = 80) -> list[NewsItem]:
    params = {
        "tags": "story",
        "numericFilters": f"created_at_i>{int(since.timestamp())},points>{min_points}",
        "hitsPerPage": 100,
    }
    with http_client() as client:
        resp = client.get(HN_SEARCH, params=params)
        resp.raise_for_status()
    items = []
    for hit in resp.json()["hits"]:
        url = hit.get("url")
        title = clean(hit.get("title", ""), 200)
        category = categorize(title)
        if not url or not category:
            continue
        source = source_from_domain(url.split("/")[2]) if "//" in url else "Hacker News"
        items.append(
            NewsItem(
                id=item_id(url),
                title=title,
                url=url,
                source=source,
                published=datetime.fromtimestamp(hit["created_at_i"], UTC).isoformat(),
                summary=clean(hit.get("story_text") or ""),
                category=category,
                tags=compute_tags(title, category=category),
                score=min(2.0, hit.get("points", 0) / 300) * CATEGORY_WEIGHT[category] * 0.9,
            )
        )
    return items


META_RE = re.compile(r"<meta\s+[^>]*>", re.IGNORECASE)
ATTR_RE = re.compile(r'(\w[\w:-]*)\s*=\s*("([^"]*)"|\'([^\']*)\')')


def fetch_article_details(url: str) -> dict[str, str]:
    """Publisher name and description from an article's <meta> tags (no body text is used)."""
    with http_client(timeout=12) as client:
        resp = client.get(url)
        resp.raise_for_status()
    found: dict[str, str] = {}
    for tag in META_RE.findall(resp.text[:300_000]):
        attrs = {m.group(1).lower(): m.group(3) if m.group(3) is not None else m.group(4)
                 for m in ATTR_RE.finditer(tag)}
        key = (attrs.get("property") or attrs.get("name") or "").lower()
        if key in {"og:site_name", "og:description", "description", "twitter:description"}:
            found.setdefault(key, clean(attrs.get("content", ""), 600))
    return {
        "site_name": found.get("og:site_name", ""),
        "description": found.get("og:description") or found.get("description")
        or found.get("twitter:description", ""),
    }


def merge_duplicates(items: list[NewsItem], threshold: float = 0.5) -> list[NewsItem]:
    merged: list[tuple[NewsItem, set[str]]] = []
    for item in sorted(items, key=lambda i: -i.score):
        toks = tokens(item.title)
        for i, (kept, kept_toks) in enumerate(merged):
            union = toks | kept_toks
            if union and len(toks & kept_toks) / len(union) >= threshold:
                merged[i] = (
                    kept.model_copy(
                        update={
                            "coverage": kept.coverage + 1,
                            "tags": list(dict.fromkeys(kept.tags + item.tags)),
                            "score": kept.score + 0.5 * item.score,
                            "summary": kept.summary or item.summary,
                        }
                    ),
                    kept_toks,
                )
                break
        else:
            merged.append((item, toks))
    return [m for m, _ in merged]


def fetch_live_news(hours: int = 30) -> list[NewsItem]:
    since = datetime.now(UTC) - timedelta(hours=hours)
    jobs = [lambda s=s, u=u: fetch_rss(s, u, since) for s, u in RSS_FEEDS]
    jobs += [lambda s=s, u=u, m=m: fetch_rss(s, u, since, m, finance_feed=True)
             for s, u, m in FINANCE_FEEDS]
    jobs.append(lambda: fetch_hacker_news(since))
    items: list[NewsItem] = []

    def run(job) -> list[NewsItem]:
        try:
            return job()
        except Exception as exc:  # noqa: BLE001
            log.warning("news source failed: %s", exc)
            return []

    with ThreadPoolExecutor(max_workers=6) as pool:
        for batch in pool.map(run, jobs):
            items.extend(batch)
    return sorted(merge_duplicates(items), key=lambda i: -i.score)


SAMPLE_NEWS = [
    ("AI", "Open-weight model tops coding benchmark, rivaling closed systems",
     ("A new open-weight language model matched leading proprietary systems on a widely used "
     "coding benchmark, while running on a single high-end GPU."), "Sample Wire", 2.4),
    ("AI", "Chipmaker unveils inference accelerator aimed at data centers",
     ("The accelerator promises lower cost per token for serving large models and ships to "
     "cloud providers next quarter."), "Sample Tech Daily", 2.1),
    ("Tech", "Regulators propose new rules for app store payments",
     ("The draft rules would let developers steer customers to outside payment options and cap "
     "commission fees."), "Sample Policy Review", 1.6),
    ("AI", "Hospital network pilots AI assistant for clinical notes",
     ("Doctors in the pilot spent less time on paperwork, though the network says every note is "
     "still reviewed by a clinician."), "Sample Health Tech", 1.5),
    ("Tech", "Quantum computing startup reports error-correction milestone",
     ("Researchers kept a logical qubit stable longer than its physical qubits, a key step toward "
     "practical machines."), "Sample Science Desk", 1.3),
    ("Biotech", "AI-designed protein enters early clinical trial",
     ("Researchers say the protein, designed with a generative model, will be tested for safety in "
     "a small first-in-human study."), "Sample Bio Journal", 1.7),
    ("AI", "Search giant adds agent mode to its browser",
     ("The feature can fill forms and compare products across sites, with confirmation prompts "
     "before purchases."), "Sample Wire", 1.2),
]


SAMPLE_SITE_NEWS = [
    (None, "Stocks climb as investors bet on a Fed rate cut",
     ("The S&P 500 and Nasdaq rose as traders priced in lower interest rates before the next Fed "
     "meeting."), "Sample Markets Wire", 1.8, 3),
    (None, "Treasury yields slip after softer inflation data",
     "Bond investors welcomed a cooler inflation reading, pushing yields lower across the curve.",
     "Sample Markets Wire", 1.5, 9),
    (None, "Bank earnings beat forecasts on strong trading revenue",
     "Large banks reported higher trading income, offsetting weaker lending growth.",
     "Sample Finance Daily", 1.4, 30),
    ("AI", "Bank rolls out AI assistant to speed up fraud investigations",
     ("Analysts at the bank use the assistant to summarize cases, with every decision still made "
     "by a human reviewer."), "Sample Fintech Review", 1.9, 5),
    ("AI", "Chipmaker shares rally as investors weigh AI demand for data centers",
     ("Shares of AI chip suppliers rose after cloud providers raised spending plans for "
     "accelerators."), "Sample Markets Wire", 2.0, 14),
    ("AI", "Payments startup raises funding to build AI agents for lending",
     ("The fintech says its agents prepare loan files for underwriters, who approve every "
     "decision."), "Sample Fintech Review", 1.3, 52),
    (None, "Wall Street watches earnings season for signs of slowing growth",
     "Investors expect mixed results as companies guide cautiously on spending.",
     "Sample Finance Daily", 1.2, 76),
    ("AI", "Insurers test machine learning models to price claims faster",
     "Several insurers piloted models that flag complex claims for adjusters, the report says.",
     "Sample Fintech Review", 1.1, 100),
    ("Tech", "Cloud provider cuts prices on storage for AI workloads",
     "The price cut targets customers training large models and storing datasets.",
     "Sample Tech Daily", 1.2, 28),
    ("Tech", "Smartphone makers prepare on-device AI features for next year",
     "Handset makers plan local language models that run without a network connection.",
     "Sample Policy Review", 1.0, 58),
    ("AI", "Researchers publish an open dataset for training coding assistants",
     "The dataset covers a dozen languages and carries a permissive license.",
     "Sample Wire", 1.4, 40),
    ("Biotech", "Gene therapy developer reports positive early trial data",
     ("Researchers saw improved outcomes in a small group of patients, and a larger study is "
     "planned."), "Sample Bio Journal", 1.5, 70),
    ("Biotech", "Drugmaker licenses AI platform to find new antibody candidates",
     ("The deal gives the drugmaker access to a model that proposes antibody designs for lab "
     "testing."), "Sample Health Tech", 1.3, 120),
    ("AI", "Regulators publish guidance on AI use in credit decisions",
     "The guidance asks lenders to explain automated decisions and to monitor models for bias.",
     "Sample Policy Review", 1.6, 140),
]


def _sample(entries: list[tuple], start: int, spread: bool) -> list[NewsItem]:
    now = datetime.now(UTC)
    items = []
    for n, entry in enumerate(entries, start):
        cat, title, summary, source, score, *rest = entry
        hours = rest[0] if spread else n
        text = f"{title} {summary}"
        items.append(NewsItem(
            id=item_id(f"https://example.com/sample/{n}"),
            title=title,
            url=f"https://example.com/sample/{n}",
            source=source,
            published=(now - timedelta(hours=hours + 1)).isoformat(),
            summary=summary,
            category=cat or categorize(text) or "Tech",
            tags=compute_tags(text, not cat, cat),
            from_feed=True,
            score=score,
        ))
    return items


def sample_news() -> list[NewsItem]:
    return _sample(SAMPLE_NEWS, 0, spread=False)


def sample_site_news() -> list[NewsItem]:
    return sample_news() + _sample(SAMPLE_SITE_NEWS, len(SAMPLE_NEWS), spread=True)


def get_news(offline: bool, hours: int = 30) -> list[NewsItem]:
    if offline:
        return sample_news()
    items = [i for i in fetch_live_news(hours) if is_video_item(i)]
    if not items:
        log.error("no live news found; using sample news")
        return sample_news()
    return items


def get_site_news(offline: bool, hours: int = 168) -> list[NewsItem]:
    if offline:
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        return [i for i in sample_site_news() if datetime.fromisoformat(i.published) >= cutoff]
    items = fetch_live_news(hours)
    if not items:
        log.error("no live site news found; using sample news")
        return sample_site_news()
    return items

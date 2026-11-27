from __future__ import annotations

import logging
import math
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta

from newsroom_core.config import INDICES, WATCHLIST
from newsroom_core.models import MarketSnapshot, PricePoint, Quote
from newsroom_core.net import http_client

log = logging.getLogger(__name__)

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


def _quote_from_series(symbol: str, name: str, points: list[PricePoint]) -> Quote:
    last, prev = points[-1].close, points[-2].close
    change = last - prev
    return Quote(
        symbol=symbol,
        name=name,
        price=round(last, 2),
        change=round(change, 2),
        change_pct=round(change / prev * 100, 2),
        series=points,
    )


def fetch_yahoo_quote(symbol: str, name: str) -> Quote:
    with http_client() as client:
        resp = client.get(YAHOO_CHART.format(symbol=symbol), params={"range": "1mo", "interval": "1d"})
        resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    closes = result["indicators"]["quote"][0]["close"]
    points = [
        PricePoint(date=datetime.fromtimestamp(ts, UTC).date().isoformat(), close=round(c, 2))
        for ts, c in zip(result["timestamp"], closes, strict=False)
        if c is not None
    ]
    if len(points) < 2:
        raise ValueError(f"not enough history for {symbol}")
    return _quote_from_series(symbol, name, points)


def fetch_live_snapshot() -> MarketSnapshot:
    symbols = {**INDICES, **WATCHLIST}
    quotes: dict[str, Quote] = {}

    def fetch(item: tuple[str, str]) -> None:
        symbol, name = item
        try:
            quotes[symbol] = fetch_yahoo_quote(symbol, name)
        except Exception as exc:  # noqa: BLE001
            log.warning("quote %s failed: %s", symbol, exc)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(fetch, symbols.items()))

    indices = [quotes[s] for s in INDICES if s in quotes]
    if not indices:
        raise RuntimeError("no index quotes available")
    return MarketSnapshot(
        as_of=indices[0].series[-1].date,
        indices=indices,
        watchlist=[quotes[s] for s in WATCHLIST if s in quotes],
    )


_SAMPLE_BASE = {
    "^GSPC": 6100.0, "^IXIC": 19800.0, "^DJI": 44200.0, "NVDA": 182.0, "MSFT": 512.0,
    "AAPL": 238.0, "GOOGL": 205.0, "AMZN": 231.0, "META": 712.0, "TSLA": 345.0, "AMD": 168.0,
    "AVGO": 301.0, "TSM": 236.0, "ORCL": 248.0, "PLTR": 154.0,
    "MRNA": 31.0, "VRTX": 452.0, "REGN": 612.0, "RXRX": 6.2,
}


def sample_snapshot(as_of: date | None = None) -> MarketSnapshot:
    as_of = as_of or date.today()
    rng = random.Random(as_of.toordinal())
    days = []
    d = as_of
    while len(days) < 22:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    days.reverse()

    def series(symbol: str) -> list[PricePoint]:
        price = _SAMPLE_BASE[symbol]
        vol = 0.008 if symbol.startswith("^") else 0.022
        drift = rng.uniform(-0.002, 0.003)
        pts = []
        for i, day in enumerate(days):
            price *= 1 + drift + rng.gauss(0, vol) + 0.002 * math.sin(i / 3)
            pts.append(PricePoint(date=day.isoformat(), close=round(price, 2)))
        return pts

    return MarketSnapshot(
        as_of=days[-1].isoformat(),
        indices=[_quote_from_series(s, n, series(s)) for s, n in INDICES.items()],
        watchlist=[_quote_from_series(s, n, series(s)) for s, n in WATCHLIST.items()],
        sample_data=True,
    )


HISTORY_DAYS = {"1mo": 22, "6mo": 126, "1y": 252}


def symbol_name(symbol: str) -> str:
    names = {**INDICES, **WATCHLIST}
    if symbol not in names:
        raise ValueError(f"unknown symbol {symbol!r}")
    return names[symbol]


def fetch_yahoo_history(symbol: str, range_: str) -> list[PricePoint]:
    with http_client() as client:
        resp = client.get(YAHOO_CHART.format(symbol=symbol),
                          params={"range": range_, "interval": "1d"})
        resp.raise_for_status()
    result = resp.json()["chart"]["result"][0]
    closes = result["indicators"]["quote"][0]["close"]
    points = [
        PricePoint(date=datetime.fromtimestamp(ts, UTC).date().isoformat(), close=round(c, 2))
        for ts, c in zip(result["timestamp"], closes, strict=False)
        if c is not None
    ]
    if len(points) < 2:
        raise ValueError(f"not enough history for {symbol}")
    return points


def sample_history(symbol: str, range_: str, as_of: date | None = None) -> list[PricePoint]:
    as_of = as_of or date.today()
    rng = random.Random(f"{symbol}-{range_}-{as_of.toordinal()}")
    days, d = [], as_of
    while len(days) < HISTORY_DAYS[range_]:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    days.reverse()
    price = _SAMPLE_BASE[symbol]
    vol = 0.008 if symbol.startswith("^") else 0.022
    drift = rng.uniform(-0.0005, 0.0015)
    points = []
    for i, day in enumerate(days):
        price *= 1 + drift + rng.gauss(0, vol) + 0.002 * math.sin(i / 7)
        points.append(PricePoint(date=day.isoformat(), close=round(price, 2)))
    return points


def get_history(symbol: str, range_: str, offline: bool) -> list[PricePoint]:
    symbol_name(symbol)
    if range_ not in HISTORY_DAYS:
        raise ValueError(f"range must be one of {', '.join(HISTORY_DAYS)}")
    if offline:
        return sample_history(symbol, range_)
    try:
        return fetch_yahoo_history(symbol, range_)
    except Exception as exc:  # noqa: BLE001
        log.error("history for %s failed (%s); using sample data", symbol, exc)
        return sample_history(symbol, range_)


def get_snapshot(offline: bool) -> MarketSnapshot:
    if offline:
        return sample_snapshot()
    try:
        return fetch_live_snapshot()
    except Exception as exc:  # noqa: BLE001
        log.error("live market data failed (%s); using sample data", exc)
        return sample_snapshot()

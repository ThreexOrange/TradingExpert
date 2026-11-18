#!/usr/bin/env python3
"""Footprint bars and order-flow signals from tick trades (definitions in references/concepts.md).

Input: trades with time, price, quantity and aggressor side. Supported:
  * Binance aggTrades CSV or zip (data.binance.vision, futures/um/daily/aggTrades):
      agg_trade_id,price,quantity,first_trade_id,last_trade_id,transact_time,is_buyer_maker
    is_buyer_maker=true means the SELLER was aggressive (counts as bid volume).
  * Generic CSV with columns time,price,qty,side (side = buy|sell for the aggressor; time in ms or ISO).

Output: one row per bar (JSON lines or CSV) with OHLC, volume, delta, max/min delta, POC and its position,
top/bottom ratios, stacked-imbalance zones and signal flags. Only trades inside a bar are used for that bar;
nothing looks forward.

Examples:
  python footprint.py BTCUSDT-aggTrades-2025-01-02.zip --tick 0.1 --rows 50 --bar 30min --out bars.jsonl
  python footprint.py --selftest

Thresholds from the book: imbalance 3x (diagonal), stacked >= 3 levels, big print ratio < 0.699,
small print ratio > 28. Others (min volume, absorption cut-offs, dominance) are this skill's additions;
see references/quant-mapping.md.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import median


@dataclass
class Params:
    tick: float = 0.01          # instrument tick size
    rows: int = 1               # ticks per footprint row
    bar_ms: int = 30 * 60_000   # bar length
    imb_ratio: float = 3.0      # book: 300 %
    imb_min_vol: float = 0.0    # added: numerator must be at least this
    stack_min: int = 3          # book: 3 consecutive levels
    big_ratio: float = 0.699    # book
    big_mult: float = 1.5       # added: extreme-level volume vs the bar's mean per-level volume
    small_ratio: float = 28.0   # book
    absorb_delta: float = 0.10  # added: |delta| / volume
    absorb_vol_mult: float = 1.5  # added: volume vs median of previous 20 bars
    dominance: float = 1.5      # added: ask total vs bid total for the quality checklist


@dataclass
class Bar:
    start: int
    open: float = math.nan
    high: float = -math.inf
    low: float = math.inf
    close: float = math.nan
    bid: dict = field(default_factory=lambda: defaultdict(float))   # level -> aggressive sell volume
    ask: dict = field(default_factory=lambda: defaultdict(float))   # level -> aggressive buy volume
    delta: float = 0.0
    max_delta: float = -math.inf
    min_delta: float = math.inf

    def add(self, price: float, qty: float, buy: bool, level: int) -> None:
        if math.isnan(self.open):
            self.open = price
        self.high, self.low, self.close = max(self.high, price), min(self.low, price), price
        (self.ask if buy else self.bid)[level] += qty
        self.delta += qty if buy else -qty
        self.max_delta, self.min_delta = max(self.max_delta, self.delta), min(self.min_delta, self.delta)


def parse_time(v: str) -> int:
    v = v.strip()
    if v.replace(".", "", 1).isdigit():
        x = float(v)
        return int(x / 1000) if x > 1e14 else int(x)          # microseconds -> ms
    t = datetime.fromisoformat(v.replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return int(t.timestamp() * 1000)


def read_trades(path: str):
    """Yield (time_ms, price, qty, aggressor_is_buyer) in file order."""
    if path.endswith(".zip"):
        z = zipfile.ZipFile(path)
        fh = io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8")
    else:
        fh = open(path, encoding="utf-8")
    rows = csv.reader(fh)
    first = next(rows)
    header = [c.strip().lower() for c in first]
    if "is_buyer_maker" in header:
        idx = {k: header.index(k) for k in ("price", "quantity", "transact_time", "is_buyer_maker")}
        it = rows
    elif len(first) == 7:                                    # headerless Binance file
        idx = {"price": 1, "quantity": 2, "transact_time": 5, "is_buyer_maker": 6}
        it = [first] + list(rows)
    else:
        idx = None
    if idx:
        for r in it:
            maker = r[idx["is_buyer_maker"]].strip().lower() in ("true", "1")
            yield parse_time(r[idx["transact_time"]]), float(r[idx["price"]]), float(r[idx["quantity"]]), not maker
        return
    k = {c: header.index(c) for c in ("time", "price", "qty", "side")}
    for r in rows:
        yield parse_time(r[k["time"]]), float(r[k["price"]]), float(r[k["qty"]]), r[k["side"]].strip().lower() == "buy"


def build_bars(trades, p: Params) -> list[Bar]:
    bars: list[Bar] = []
    step = p.tick * p.rows
    for t, price, qty, buy in trades:
        start = t - t % p.bar_ms
        if not bars or bars[-1].start != start:
            if bars and start < bars[-1].start:
                raise ValueError("trades must be in time order")
            bars.append(Bar(start))
        bars[-1].add(price, qty, buy, int(math.floor(price / step + 1e-9)))
    return bars


def imbalances(b: Bar, p: Params) -> tuple[list[int], list[int]]:
    """Diagonal: buy at L if ask(L) >= k*bid(L-1); sell at L if bid(L) >= k*ask(L+1)."""
    levels = sorted(set(b.ask) | set(b.bid))
    lo, hi = levels[0], levels[-1]
    buy, sell = [], []
    for L in levels:
        # the diagonal cell must lie inside the bar's range: the lowest row has no bid below it to compare with
        if L - 1 >= lo:
            a, d = b.ask.get(L, 0.0), b.bid.get(L - 1, 0.0)
            if a >= max(p.imb_min_vol, 1e-12) and a >= p.imb_ratio * d:
                buy.append(L)
        if L + 1 <= hi:
            s, u = b.bid.get(L, 0.0), b.ask.get(L + 1, 0.0)
            if s >= max(p.imb_min_vol, 1e-12) and s >= p.imb_ratio * u:
                sell.append(L)
    return buy, sell


def stacks(levels: list[int], n: int) -> list[tuple[int, int]]:
    out, run = [], []
    for L in sorted(levels):
        if run and L == run[-1] + 1:
            run.append(L)
        else:
            if len(run) >= n:
                out.append((run[0], run[-1]))
            run = [L]
    if len(run) >= n:
        out.append((run[0], run[-1]))
    return out


def ratio(num: float, den: float) -> float:
    return math.inf if den == 0 else num / den


def analyse(bars: list[Bar], p: Params) -> list[dict]:
    step = p.tick * p.rows
    rows, vols = [], []
    prev = None
    for b in bars:
        levels = sorted(set(b.ask) | set(b.bid))
        vol_at = {L: b.ask.get(L, 0.0) + b.bid.get(L, 0.0) for L in levels}
        vol = sum(vol_at.values())
        poc = max(levels, key=lambda L: vol_at[L])
        rng = b.high - b.low
        poc_pos = (poc * step - b.low) / rng if rng > 0 else 0.5
        top, top2 = levels[-1], (levels[-2] if len(levels) > 1 else None)
        bot, bot2 = levels[0], (levels[1] if len(levels) > 1 else None)
        top_ratio = ratio(b.ask.get(top2, 0.0), b.ask.get(top, 0.0)) if top2 is not None else math.nan
        bot_ratio = ratio(b.bid.get(bot2, 0.0), b.bid.get(bot, 0.0)) if bot2 is not None else math.nan
        mean_lvl = vol / len(levels)
        buy_imb, sell_imb = imbalances(b, p)
        buy_stacks, sell_stacks = stacks(buy_imb, p.stack_min), stacks(sell_imb, p.stack_min)
        close_pos = (b.close - b.low) / rng if rng > 0 else 0.5
        big_top = top_ratio < p.big_ratio and b.ask.get(top, 0.0) >= p.big_mult * mean_lvl
        big_bot = bot_ratio < p.big_ratio and b.bid.get(bot, 0.0) >= p.big_mult * mean_lvl
        med20 = median(vols[-20:]) if len(vols) >= 5 else math.nan
        r = {
            "start": datetime.fromtimestamp(b.start / 1000, tz=timezone.utc).isoformat(),
            "open": b.open, "high": b.high, "low": b.low, "close": b.close,
            "volume": vol, "ask_total": sum(b.ask.values()), "bid_total": sum(b.bid.values()),
            "delta": b.delta, "max_delta": b.max_delta, "min_delta": b.min_delta,
            "delta_ratio": b.delta / vol if vol else 0.0,
            "poc": poc * step, "poc_pos": round(poc_pos, 3),
            "top_ratio": top_ratio, "bottom_ratio": bot_ratio,
            "buy_imbalances": len(buy_imb), "sell_imbalances": len(sell_imb),
            "buy_stacks": [[lo * step, hi * step] for lo, hi in buy_stacks],
            "sell_stacks": [[lo * step, hi * step] for lo, hi in sell_stacks],
            # signals
            "poc_bottom_bullish": poc_pos < 1 / 3 and b.close > poc * step,
            "poc_top_bearish": poc_pos > 2 / 3 and b.close < poc * step,
            "big_print_top": big_top, "big_print_bottom": big_bot,
            "small_print_top": top_ratio > p.small_ratio, "small_print_bottom": bot_ratio > p.small_ratio,
            "trapped_longs": (any(L >= top - 1 for L in buy_imb) or big_top) and close_pos < 1 / 3,
            "trapped_shorts": (any(L <= bot + 1 for L in sell_imb) or big_bot) and close_pos > 2 / 3,
            "absorption": vol > 0 and abs(b.delta) / vol <= p.absorb_delta and not math.isnan(med20)
                          and vol >= p.absorb_vol_mult * med20,
            "bearish_divergence": prev is not None and b.high > prev.high and b.delta < 0 and b.close < b.open,
            "bullish_divergence": prev is not None and b.low < prev.low and b.delta > 0 and b.close > b.open,
            "quality_long": b.delta > 0 and b.close > b.open and sum(b.ask.values()) >= p.dominance * sum(b.bid.values()),
            "quality_short": b.delta < 0 and b.close < b.open and sum(b.bid.values()) >= p.dominance * sum(b.ask.values()),
        }
        rows.append(r)
        vols.append(vol)
        prev = b
    return rows


def selftest() -> None:
    """Synthetic bars that must trigger specific signals."""
    p = Params(tick=1, rows=1, bar_ms=60_000)
    trades = []
    t0 = 1_700_000_000_000
    # bar 1: up bar with a stacked buy imbalance at 101-103 and a big print at the top (105)
    for px, a, b_ in [(100, 10, 10), (101, 40, 10), (102, 45, 10), (103, 50, 10), (104, 20, 15), (105, 120, 5)]:
        trades += [(t0, px, a, True), (t0 + 1, px, b_, False)]
    trades.append((t0 + 2, 104, 1, True))                       # close below the top
    # bar 2: down bar, small print at the bottom (1 lot at 95 vs 40 at 96), delta negative, new low
    t1 = t0 + 60_000
    for px, a, b_ in [(99, 5, 30), (98, 5, 35), (97, 5, 30), (96, 5, 40), (95, 0, 1)]:
        trades += [(t1, px, a, True), (t1 + 1, px, b_, False)]
    trades.append((t1 + 2, 96, 2, False))
    bars = build_bars(sorted(trades, key=lambda x: x[0]), p)
    out = analyse(bars, p)
    assert len(out) == 2, out
    a, b = out
    assert a["buy_stacks"] == [[101.0, 103.0]], a["buy_stacks"]
    assert a["big_print_top"] and a["top_ratio"] < 0.699, a
    assert b["small_print_bottom"] and b["bottom_ratio"] > 28, b
    assert b["delta"] < 0 and b["low"] < a["low"]
    print("selftest ok:", json.dumps({k: a[k] for k in ("delta", "poc", "top_ratio", "buy_stacks")}),
          json.dumps({k: b[k] for k in ("delta", "bottom_ratio", "small_print_bottom")}))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("trades", nargs="?")
    ap.add_argument("--tick", type=float, default=0.01)
    ap.add_argument("--rows", type=int, default=1, help="ticks per footprint row")
    ap.add_argument("--bar", default="30min", help="bar length, e.g. 5min, 30min, 1h")
    ap.add_argument("--imb", type=float, default=3.0)
    ap.add_argument("--min-vol", type=float, default=0.0)
    ap.add_argument("--out", default="-", help=".jsonl or .csv; '-' prints JSON lines")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return
    if not a.trades:
        ap.error("trades file required")
    unit = {"min": 60_000, "h": 3_600_000, "s": 1000}
    num = "".join(ch for ch in a.bar if ch.isdigit()) or "1"
    suf = a.bar[len(num):]
    p = Params(tick=a.tick, rows=a.rows, bar_ms=int(num) * unit[suf], imb_ratio=a.imb, imb_min_vol=a.min_vol)
    rows = analyse(build_bars(read_trades(a.trades), p), p)
    if a.out.endswith(".csv"):
        with open(a.out, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            for r in rows:
                w.writerow({k: json.dumps(v) if isinstance(v, list) else v for k, v in r.items()})
    else:
        fh = sys.stdout if a.out == "-" else open(a.out, "w", encoding="utf-8")
        for r in rows:
            fh.write(json.dumps(r, default=str) + "\n")
    print(f"{len(rows)} bars", file=sys.stderr)


if __name__ == "__main__":
    main()

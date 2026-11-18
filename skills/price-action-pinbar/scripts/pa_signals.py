#!/usr/bin/env python3
"""Price-action signals with the book's 2+5 scoring, computed bar by bar from closed bars only.

CSV input: time,open,high,low,close[,volume] in time order (any timezone string; it is passed through).
Output: one row per detected signal with pattern, the two basic conditions, the five details, entry, stop,
target, reward/risk and whether it is tradable (both basics and >= 2 details). See references/quant-mapping.md
for which thresholds come from the book and which were added to make the rules computable.

  python pa_signals.py bars.csv --out signals.csv
  python pa_signals.py --selftest

Key levels are built only from pivots that were already confirmed (n bars after the pivot) when the signal bar
closed, so nothing is drawn back in time.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys

PIVOT_N = 5          # added: bars on each side of a turning point
PIVOT_MOVE = 1.5     # added: a turning point counts if price moved >= 1.5 ATR away within PIVOT_N bars
CLUSTER = 0.5        # added: pivots within 0.5 ATR form one level
NEAR = 0.5           # added: wick end within 0.5 ATR of a level = "at a key level"
EXTREME_N = 10       # added: signal extreme must be the extreme of the last 10 bars
TREND_N = 3          # book: at least 3 bars of trend before the signal
PROMINENT = 1.0      # added: signal range >= 1 ATR
TREND_MA = 100       # added: larger-trend filter
MIN_RR = 1.5         # book


def atr(h, l, c, n=14):
    out, prev = [math.nan] * len(c), None
    for i in range(len(c)):
        tr = h[i] - l[i] if i == 0 else max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        prev = tr if prev is None else prev + (tr - prev) / n
        out[i] = prev if i >= n - 1 else math.nan
    return out


def sma(x, n):
    out, s = [math.nan] * len(x), 0.0
    for i, v in enumerate(x):
        s += v
        if i >= n:
            s -= x[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def pivots(h, l, a):
    """(confirm_index, price, kind, scale) for obvious turning points, confirmed PIVOT_N bars later."""
    n, out = PIVOT_N, []
    for i in range(n, len(h) - n):
        if math.isnan(a[i]):
            continue
        if h[i] > max(h[i - n:i]) and h[i] >= max(h[i + 1:i + n + 1]) and h[i] - min(l[i + 1:i + n + 1]) >= PIVOT_MOVE * a[i]:
            out.append((i + n, h[i], "high", i))
        if l[i] < min(l[i - n:i]) and l[i] <= min(l[i + 1:i + n + 1]) and max(h[i + 1:i + n + 1]) - l[i] >= PIVOT_MOVE * a[i]:
            out.append((i + n, l[i], "low", i))
    return out


def levels_at(piv, t, a_t):
    """Cluster the pivots confirmed before bar t into horizontal levels (price = most recent pivot in cluster)."""
    known = sorted((p for p in piv if p[0] < t), key=lambda p: p[1])
    levels, cur = [], []
    for p in known:
        if cur and p[1] - cur[-1][1] > CLUSTER * a_t:
            levels.append(cur)
            cur = []
        cur.append(p)
    if cur:
        levels.append(cur)
    out = []
    for grp in levels:
        last = max(grp, key=lambda p: p[3])
        out.append({"price": last[1], "touches": len(grp), "last_pivot": last[3]})
    return out


def is_pin(o, h, l, c, bull):
    r = h - l
    if r <= 0:
        return False
    wick = (min(o, c) - l) if bull else (h - max(o, c))
    return wick >= 2 / 3 * r


def candidates(O, H, L, C, t):
    """Patterns ending at bar t: single pinbar, 2-bar engulfing, 3-bar star; merged OHLC must be a pinbar."""
    out = []
    for bull in (True, False):
        if is_pin(O[t], H[t], L[t], C[t], bull):
            out.append(("pinbar", bull, t))
        if t >= 1:
            o1, c1, o2, c2 = O[t - 1], C[t - 1], O[t], C[t]
            engulf = (c1 < o1 and c2 > o2 and c2 >= o1 and o2 <= c1) if bull else (c1 > o1 and c2 < o2 and c2 <= o1 and o2 >= c1)
            if engulf and is_pin(o1, max(H[t - 1:t + 1]), min(L[t - 1:t + 1]), c2, bull):
                out.append(("engulfing", bull, t - 1))
        if t >= 2:
            o1, c1 = O[t - 2], C[t - 2]
            first_ok = (c1 < o1) if bull else (c1 > o1)
            last_ok = (C[t] > O[t]) if bull else (C[t] < O[t])
            small_mid = abs(C[t - 1] - O[t - 1]) <= 0.5 * abs(c1 - o1)
            same = sum(1 for k in range(t - 2, t + 1) if (C[k] > O[k]) == bull)
            if first_ok and last_ok and small_mid and same <= 3 - same and \
                    is_pin(o1, max(H[t - 2:t + 1]), min(L[t - 2:t + 1]), C[t], bull):
                out.append(("star", bull, t - 2))
    return out


def scan(rows):
    T = [r["time"] for r in rows]
    O, H, L, C = ([float(r[k]) for r in rows] for k in ("open", "high", "low", "close"))
    A = atr(H, L, C)
    M = sma(C, TREND_MA)
    piv = pivots(H, L, A)
    sigs = []
    for t in range(max(TREND_MA + 20, EXTREME_N + TREND_N + 2), len(C)):
        a = A[t]
        if math.isnan(a):
            continue
        lv = levels_at(piv, t, a)
        for pattern, bull, s in candidates(O, H, L, C, t):
            o, h, l, c = O[s], max(H[s:t + 1]), min(L[s:t + 1]), C[t]
            rng = h - l
            wick_end = l if bull else h
            body_lo, body_hi = min(o, c), max(o, c)
            near = [x for x in lv if abs(x["price"] - wick_end) <= NEAR * a
                    or (bull and l < x["price"] < body_lo) or (not bull and body_hi < x["price"] < h)]
            basic_level = bool(near)
            win = range(t - EXTREME_N + 1, t + 1)
            extreme = (l <= min(L[k] for k in win)) if bull else (h >= max(H[k] for k in win))
            trend_in = (C[s - 1] < C[s - 1 - TREND_N]) if bull else (C[s - 1] > C[s - 1 - TREND_N])
            basic_extreme = extreme and trend_in
            d_prominent = rng >= PROMINENT * a
            d_false_break = any((bull and l < x["price"] < c) or (not bull and c < x["price"] < h) for x in lv)
            le = s - 1
            d_left_eye = L[le] <= body_lo and body_hi <= H[le] and rng > H[le] - L[le]
            d_trend = (c > M[t] and M[t] > M[t - 20]) if bull else (c < M[t] and M[t] < M[t - 20])
            entry, stop = (h, l) if bull else (l, h)
            ahead = sorted((x["price"] for x in lv if (x["price"] > entry + 0.1 * a if bull else x["price"] < entry - 0.1 * a)),
                           reverse=not bull)
            target = ahead[0] if ahead else math.nan
            rr = abs(target - entry) / rng if ahead and rng > 0 else math.nan
            d_rr = not math.isnan(rr) and rr >= MIN_RR
            details = [d_prominent, d_false_break, d_left_eye, d_trend, d_rr]
            sigs.append({
                "time": T[t], "direction": "long" if bull else "short", "pattern": pattern,
                "basic_at_level": basic_level, "basic_extreme": basic_extreme,
                "prominent": d_prominent, "false_break": d_false_break, "left_eye": d_left_eye,
                "with_trend": d_trend, "rr_ok": d_rr, "details": sum(details),
                "tradable": basic_level and basic_extreme and sum(details) >= 2,
                "entry": entry, "stop": stop, "stop_50pct": (l + h) / 2, "target": target,
                "rr": round(rr, 2) if not math.isnan(rr) else None,
                "retrace_50_entry": (l + h) / 2, "atr": a,
            })
    return sigs


def selftest():
    """A market that rallies from a base, falls back into it, and prints a bullish pinbar with a false break."""
    rows, p = [], 100.0
    def bar(o, h, l, c):
        rows.append({"time": str(len(rows)), "open": o, "high": h, "low": l, "close": c})
    for i in range(130):                    # long gentle uptrend so the 100-bar mean rises
        bar(p, p + 1.2, p - 1.0, p + 0.3); p += 0.3
    base = p
    for i in range(6):                      # sharp drop to a clear low (turning point)
        bar(p, p + 0.5, p - 3.0, p - 2.5); p -= 2.5
    low = p - 0.5
    for i in range(12):                     # strong rebound well above the low
        bar(p, p + 2.5, p - 0.3, p + 2.0); p += 2.0
    for i in range(10):                     # fall back toward the old low, closes stepping down
        bar(p, p + 0.4, p - 1.8, p - 1.5); p -= 1.5
    o = p
    bar(o, o + 0.5, low - 1.5, o + 0.2)     # pinbar: long lower wick through the old low, close back above
    sig = [s for s in scan(rows) if s["time"] == str(len(rows) - 1) and s["direction"] == "long"]
    assert sig, "no signal on the last bar"
    s = sig[0]
    assert s["pattern"] == "pinbar" and s["basic_at_level"] and s["basic_extreme"] and s["false_break"], s
    print("selftest ok:", json.dumps({k: s[k] for k in ("pattern", "basic_at_level", "basic_extreme", "false_break",
                                                         "prominent", "left_eye", "with_trend", "rr", "details", "tradable")}))
    _ = base


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bars", nargs="?")
    ap.add_argument("--out", default="-")
    ap.add_argument("--all", action="store_true", help="also print signals that are not tradable")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return
    if not a.bars:
        ap.error("bars CSV required")
    with open(a.bars, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    sigs = [s for s in scan(rows) if a.all or s["tradable"]]
    if a.out == "-":
        for s in sigs:
            print(json.dumps(s))
    else:
        with open(a.out, "w", newline="", encoding="utf-8") as fh:
            if sigs:
                w = csv.DictWriter(fh, fieldnames=list(sigs[0]))
                w.writeheader()
                w.writerows(sigs)
    print(f"{len(sigs)} signals", file=sys.stderr)


if __name__ == "__main__":
    main()

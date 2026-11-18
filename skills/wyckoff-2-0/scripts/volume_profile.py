#!/usr/bin/env python3
"""Volume profile per session (or for a fixed range) from OHLCV bars: POC, value area (70 %), HVN/LVN,
P/b/D shape, session VWAP with 1 and 2 standard-deviation bands, and naked (untested) POCs.

CSV input: time,open,high,low,close,volume in time order. time = ISO string with timezone or epoch ms.
With bars only, each bar's volume is spread evenly over the rows between its low and high (a common
approximation); with trades, aggregate them into 1-minute bars first for a close match.

  python volume_profile.py bars.csv --row 0.5 --session-hours 24 --out sessions.json
  python volume_profile.py bars.csv --row 0.5 --from 2025-01-02T00:00:00+00:00 --to 2025-01-09T00:00:00+00:00
  python volume_profile.py --selftest

Definitions and which thresholds are added (not from the book) are in references/quant-mapping.md.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone

VA_SHARE = 0.70      # book: about 68-70 %
HVN_MULT = 1.3       # added
LVN_MULT = 0.5       # added
SHAPE_SHARE = 0.60   # added


def ts(v: str) -> int:
    v = v.strip()
    if v.replace(".", "", 1).isdigit():
        x = float(v)
        return int(x / 1000) if x > 1e14 else int(x)
    t = datetime.fromisoformat(v.replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("times need a timezone")
    return int(t.timestamp() * 1000)


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return [{"t": ts(r["time"]), "o": float(r["open"]), "h": float(r["high"]), "l": float(r["low"]),
             "c": float(r["close"]), "v": float(r["volume"])} for r in rows]


def profile(bars: list[dict], row: float) -> dict[int, float]:
    prof: dict[int, float] = {}
    for b in bars:
        lo, hi = int(math.floor(b["l"] / row + 1e-9)), int(math.floor(b["h"] / row + 1e-9))
        n = hi - lo + 1
        for k in range(lo, hi + 1):
            prof[k] = prof.get(k, 0.0) + b["v"] / n
    return prof


def value_area(prof: dict[int, float]) -> tuple[int, int, int]:
    """POC, VAL, VAH (row indices). Classic rule: from the POC add the larger of the next two rows above/below."""
    levels = sorted(prof)
    total = sum(prof.values())
    mid = (levels[0] + levels[-1]) / 2
    poc = max(levels, key=lambda k: (prof[k], -abs(k - mid)))
    lo = hi = poc
    acc = prof[poc]
    while acc < VA_SHARE * total and (lo > levels[0] or hi < levels[-1]):
        up = sum(prof.get(hi + i, 0.0) for i in (1, 2)) if hi < levels[-1] else -1
        dn = sum(prof.get(lo - i, 0.0) for i in (1, 2)) if lo > levels[0] else -1
        if up >= dn:
            for i in (1, 2):
                if hi < levels[-1]:
                    hi += 1
                    acc += prof.get(hi, 0.0)
        else:
            for i in (1, 2):
                if lo > levels[0]:
                    lo -= 1
                    acc += prof.get(lo, 0.0)
    return poc, lo, hi


def nodes(prof: dict[int, float]) -> tuple[list[int], list[int]]:
    levels = list(range(min(prof), max(prof) + 1))
    raw = [prof.get(k, 0.0) for k in levels]
    sm = [sum(raw[max(0, i - 1):i + 2]) / len(raw[max(0, i - 1):i + 2]) for i in range(len(raw))]
    mean = sum(sm) / len(sm)
    hvn, lvn = [], []
    for i in range(1, len(sm) - 1):
        if sm[i] >= sm[i - 1] and sm[i] > sm[i + 1] and sm[i] >= HVN_MULT * mean:
            hvn.append(levels[i])
        if sm[i] <= sm[i - 1] and sm[i] < sm[i + 1] and sm[i] <= LVN_MULT * mean:
            lvn.append(levels[i])
    return hvn, lvn


def shape(prof: dict[int, float], poc: int) -> str:
    lo, hi = min(prof), max(prof)
    if hi == lo:
        return "D"
    pos = (poc - lo) / (hi - lo)
    total = sum(prof.values())
    upper = sum(v for k, v in prof.items() if k >= (lo + hi) / 2) / total
    if pos > 2 / 3 and upper >= SHAPE_SHARE:
        return "P"
    if pos < 1 / 3 and (1 - upper) >= SHAPE_SHARE:
        return "b"
    return "D"


def vwap_bands(bars: list[dict]) -> dict:
    pv = vol = 0.0
    for b in bars:
        tp = (b["h"] + b["l"] + b["c"]) / 3
        pv, vol = pv + tp * b["v"], vol + b["v"]
    vw = pv / vol if vol else math.nan
    var = sum(b["v"] * ((b["h"] + b["l"] + b["c"]) / 3 - vw) ** 2 for b in bars) / vol if vol else math.nan
    sd = math.sqrt(var) if var == var else math.nan
    return {"vwap": vw, "sd": sd, "up1": vw + sd, "dn1": vw - sd, "up2": vw + 2 * sd, "dn2": vw - 2 * sd}


def summarize(bars: list[dict], row: float) -> dict:
    prof = profile(bars, row)
    poc, val, vah = value_area(prof)
    hvn, lvn = nodes(prof)
    return {"start": iso(bars[0]["t"]), "end": iso(bars[-1]["t"]), "bars": len(bars),
            "volume": sum(b["v"] for b in bars), "high": max(b["h"] for b in bars), "low": min(b["l"] for b in bars),
            "poc": (poc + 0.5) * row, "val": val * row, "vah": (vah + 1) * row, "shape": shape(prof, poc),
            "hvn": [(k + 0.5) * row for k in hvn], "lvn": [(k + 0.5) * row for k in lvn], **vwap_bands(bars)}


def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


def sessions(bars: list[dict], hours: float, row: float) -> list[dict]:
    span = int(hours * 3_600_000)
    groups: dict[int, list[dict]] = {}
    for b in bars:
        groups.setdefault(b["t"] - b["t"] % span, []).append(b)
    keys = sorted(groups)
    out = []
    for i, k in enumerate(keys):
        s = summarize(groups[k], row)
        later = [b for kk in keys[i + 1:] for b in groups[kk]]
        touched = next((b for b in later if b["l"] <= s["poc"] <= b["h"]), None)
        s["poc_tested_at"] = iso(touched["t"]) if touched else None      # None = naked POC so far
        s["complete"] = i < len(keys) - 1
        out.append(s)
    return out


def selftest() -> None:
    bars, t0 = [], 1_699_920_000_000   # 2023-11-14 00:00 UTC, aligned to the session split
    price = 100.0
    for i in range(60):            # day 1: rally then a high-volume balance near 110 -> P shape
        if i < 15:
            price += 0.7
            bars.append({"t": t0 + i * 60_000 * 24, "o": price - 0.7, "h": price + 0.2, "l": price - 0.8, "c": price, "v": 50})
        else:
            p = 110 + (i % 3 - 1) * 0.4
            bars.append({"t": t0 + i * 60_000 * 24, "o": p, "h": p + 0.5, "l": p - 0.5, "c": p, "v": 400})
    day2 = t0 + 86_400_000
    for i in range(60):            # day 2 trades only above 115: day-1 POC stays naked
        p = 116 + (i % 4) * 0.3
        bars.append({"t": day2 + i * 60_000 * 24, "o": p, "h": p + 0.4, "l": p - 0.4, "c": p, "v": 100})
    out = sessions(bars, 24, 0.5)
    d1 = out[0]
    assert d1["shape"] == "P", d1
    assert 109.0 <= d1["poc"] <= 111.0 and d1["val"] < d1["poc"] < d1["vah"], d1
    assert d1["poc_tested_at"] is None, d1
    assert d1["hvn"], d1
    print("selftest ok:", json.dumps({k: (round(v, 2) if isinstance(v, float) else v)
                                     for k, v in d1.items() if k in ("poc", "val", "vah", "shape", "vwap", "poc_tested_at")}))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bars", nargs="?")
    ap.add_argument("--row", type=float, required=False, help="price per profile row")
    ap.add_argument("--session-hours", type=float, default=24.0)
    ap.add_argument("--from", dest="start")
    ap.add_argument("--to", dest="end")
    ap.add_argument("--out", default="-")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return
    if not a.bars or not a.row:
        ap.error("bars CSV and --row are required")
    bars = load(a.bars)
    if a.start or a.end:
        lo = ts(a.start) if a.start else -math.inf
        hi = ts(a.end) if a.end else math.inf
        result = summarize([b for b in bars if lo <= b["t"] < hi], a.row)
    else:
        result = sessions(bars, a.session_hours, a.row)
    text = json.dumps(result, indent=1)
    if a.out == "-":
        print(text)
    else:
        open(a.out, "w", encoding="utf-8").write(text)
        print(f"wrote {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""LWAI-inspired research lab: OHLCV-only (data level L3) prototypes of modules D, E, F
from 02_我们的指标体系设计.md, plus an event study and a simple trade simulation.

Everything here is computed bar by bar from past data only. Signals are acted on at the
NEXT bar's open. Nothing in this file is investment advice; it is a test bench.

Usage:
  python3 lwai_lab.py fetch   --cache DIR [--n 400] [--seed 7]
  python3 lwai_lab.py null    # radar echo null distribution vs F(2K, 2(M-K))
  python3 lwai_lab.py study   --cache DIR --out RESULT.md
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------- data

YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1={p1}&period2={p2}&interval=1d&events=div%2Csplits"


def candidate_codes() -> list[str]:
    """All plausible A-share codes on the main boards and ChiNext (STAR excluded: 20% limit, short history)."""
    sh = [f"{c:06d}.SS" for c in list(range(600000, 604000)) + list(range(605000, 605600))]
    sz = [f"{c:06d}.SZ" for c in list(range(1, 3100)) + list(range(300001, 301700))]
    return sh + sz


def fetch_one(sym: str, cache: str, p1: int, p2: int) -> str:
    path = os.path.join(cache, sym + ".csv")
    if os.path.exists(path):
        return "cached"
    req = urllib.request.Request(YAHOO.format(sym=sym, p1=p1, p2=p2), headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            js = json.loads(r.read().decode())
    except Exception as e:  # 404 for non-existent codes
        return "miss"
    try:
        res = js["chart"]["result"][0]
        ts = res["timestamp"]
        q = res["indicators"]["quote"][0]
        adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose")
    except Exception:
        return "miss"
    df = pd.DataFrame({"ts": ts, "open": q["open"], "high": q["high"], "low": q["low"],
                       "close": q["close"], "volume": q["volume"], "adjclose": adj if adj else q["close"]})
    df = df.dropna()
    if len(df) < 300:
        return "short"
    df["date"] = pd.to_datetime(df["ts"], unit="s", utc=True).dt.tz_convert("Asia/Shanghai").dt.date
    df.drop(columns=["ts"]).to_csv(path, index=False)
    return "ok"


def cmd_fetch(a):
    os.makedirs(a.cache, exist_ok=True)
    codes = candidate_codes()
    rnd = random.Random(a.seed)
    rnd.shuffle(codes)
    p1 = int(pd.Timestamp("2014-01-01").timestamp())
    p2 = int(pd.Timestamp("2026-11-14").timestamp())
    got = len([f for f in os.listdir(a.cache) if f.endswith(".csv")])
    extra = ["600186.SS", "600241.SS", "605178.SS", "001331.SZ", "600889.SS", "002165.SZ", "300844.SZ", "601086.SS"]
    i = 0
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(lambda s: fetch_one(s, a.cache, p1, p2), extra))
        while got < a.n and i < len(codes):
            batch = codes[i:i + 60]
            i += 60
            st = list(ex.map(lambda s: fetch_one(s, a.cache, p1, p2), batch))
            got = len([f for f in os.listdir(a.cache) if f.endswith(".csv")])
            print(f"tried {i}, have {got}", flush=True)
            time.sleep(0.5)


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df = df[(df["volume"] > 0) & (df["high"] >= df["low"])].copy()
    # back-adjust OHLC with Yahoo's adjclose factor so splits/dividends do not create fake gaps
    f = (df["adjclose"] / df["close"]).replace([np.inf, -np.inf], np.nan).ffill().fillna(1.0)
    for c in ("open", "high", "low", "close"):
        df[c] = df[c] * f
    df = df.drop_duplicates("date").set_index("date").sort_index()
    return df[["open", "high", "low", "close", "volume"]]


# ------------------------------------------------------------------------- features

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    pc = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def delta_l3(df: pd.DataFrame) -> pd.Series:
    """Level-3 delta estimate from daily bars: buy = V*CLV+, one-price bars by sign of change."""
    rng = df["high"] - df["low"]
    clv = ((df["close"] - df["low"]) / rng).where(rng > 0)
    chg = np.sign(df["close"] - df["close"].shift())
    clv = clv.fillna((chg + 1) / 2).fillna(0.5)
    return df["volume"] * (2 * clv - 1)


def close_location(df: pd.DataFrame) -> pd.Series:
    pc = df["close"].shift()
    lo = np.minimum(df["low"], pc)
    hi = np.maximum(df["high"], pc)
    return ((df["close"] - lo) / (hi - lo)).where(hi > lo, 0.5)


def radar_echo(df: pd.DataFrame, a: pd.Series, N: int = 120, K: int = 6, M: int = 30) -> pd.Series:
    """Module E echo in dB: periodogram of demeaned ATR-normalised bodies, low (1..K) vs high (K+1..M)."""
    b = ((df["close"] - df["open"]) / a).to_numpy()
    out = np.full(len(b), np.nan)
    if len(b) < N:
        return pd.Series(out, index=df.index)
    w = np.lib.stride_tricks.sliding_window_view(b, N)
    w = w - w.mean(axis=1, keepdims=True)
    X = np.fft.rfft(w, axis=1)
    p = np.abs(X) ** 2
    lo = p[:, 1:K + 1].mean(axis=1)
    hi = p[:, K + 1:M + 1].mean(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        out[N - 1:] = 10 * np.log10(lo / hi)
    return pd.Series(out, index=df.index)


def radar_lock(E: pd.Series, look: int = 200, k_in: float = 1.5, k_out: float = 0.5, floor_db: float = 3.0) -> pd.Series:
    mu = E.rolling(look, min_periods=look // 2).mean().shift()
    sd = E.rolling(look, min_periods=look // 2).std().shift()
    enter = np.maximum(floor_db, mu + k_in * sd)
    leave = mu + k_out * sd
    lock = np.zeros(len(E), dtype=bool)
    on = False
    ev, en, lv = E.to_numpy(), enter.to_numpy(), leave.to_numpy()
    for i in range(len(E)):
        if np.isnan(ev[i]) or np.isnan(en[i]):
            on = False
        elif not on and ev[i] > en[i]:
            on = True
        elif on and ev[i] < lv[i]:
            on = False
        lock[i] = on
    return pd.Series(lock, index=E.index)


def features(df: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=df.index)
    o, h, l, c, v = (df[x] for x in ("open", "high", "low", "close", "volume"))
    a = atr(df)
    f["atr"] = a
    f["ma20"] = c.rolling(20).mean()
    hh120 = h.rolling(120).max()
    ll120 = l.rolling(120).min()
    f["dd120"] = 1 - l / hh120
    f["pos120"] = (c - ll120) / (hh120 - ll120)
    f["voldry"] = v.rolling(5).mean() / v.rolling(20).mean()
    d = delta_l3(df)
    f["delta_pct"] = d / v
    f["cl"] = close_location(df)
    sell = (v - d) / 2
    # D1 latent score
    c1 = f["pos120"] <= 0.35
    c2 = f["voldry"] <= 0.7
    c3 = sell.rolling(5).sum() < sell.shift(5).rolling(5).sum()
    c4 = atr(df, 5) < 0.8 * a
    cvd = d.cumsum()
    newlow = (l <= l.rolling(20).min()).rolling(5).max().astype(bool)
    c5 = newlow & (cvd > cvd.rolling(20).min() + 0.05 * v.rolling(20).sum())
    score = 20 * (c1.astype(int) + c2.astype(int) + c3.astype(int) + c4.astype(int) + c5.astype(int))
    f["latent"] = score.where(c1 & c2, 0)
    # D2 frog
    f["frog"] = (3 * d.rolling(20).sum() / v.rolling(20).sum() * 100).clip(-100, 100)
    # E radar
    E = radar_echo(df, a)
    f["echo"] = E
    f["lock"] = radar_lock(E)
    body = (c - o) / a
    f["dir5"] = np.sign(body.rolling(5).sum())
    f["ignite_up"] = f["lock"] & ~f["lock"].shift(1, fill_value=False) & (f["dir5"] > 0) & (c > o)
    return f


def limit_features(df: pd.DataFrame, sym: str) -> pd.DataFrame:
    """A-share limit-up features: limit-up flags, 250-day limit-up count ("妖股基因"), and 单阳不破.

    单阳不破 (our definition): a limit-up day U after DD120 >= 30%; over the next 3..10 bars no close
    below U's low and 5-day volume shrinks below U's volume; signal on the first close above U's high.
    """
    c, h, l, v = df["close"], df["high"], df["low"], df["volume"]
    lim = limit_pct(sym)
    up = (c / c.shift() - 1) >= lim - 0.005
    gene = up.rolling(250, min_periods=60).sum()
    hh120 = h.rolling(120).max()
    dd_prev = 1 - l.rolling(20).min() / hh120
    cc, hh, ll, vv = c.to_numpy(), h.to_numpy(), l.to_numpy(), v.to_numpy()
    upa, dda = up.to_numpy(), dd_prev.to_numpy()
    sig = np.zeros(len(cc), bool)
    lx = np.full(len(cc), np.nan)
    last = -999
    for u in np.flatnonzero(upa):
        if u < 130 or not (dda[u] >= 0.30):
            continue
        for t in range(u + 3, min(u + 11, len(cc))):
            if cc[t - 1] < ll[u]:
                break
            if cc[t] > hh[u] and vv[u + 1:t].mean() < vv[u] and t - last >= 20:
                if cc[u + 1:t].min() >= ll[u]:
                    sig[t] = True
                    lx[t] = ll[u + 1:t + 1].min()
                    last = t
                break
    return pd.DataFrame({"limit_up": up, "gene": gene, "danyang": sig, "lx_danyang": lx}, index=df.index)


def f_signals(df: pd.DataFrame, f: pd.DataFrame, cooldown: int = 20) -> pd.DataFrame:
    """Module F: aggressive (F3a) and conservative (F3b) break-bottom-and-stand signals."""
    o, h, l, c = (df[x].to_numpy() for x in ("open", "high", "low", "close"))
    n = len(c)
    prior20 = df["low"].rolling(20).min().shift().to_numpy()
    dd = f["dd120"].rolling(6).max().to_numpy()
    ma20 = f["ma20"].to_numpy()
    cl = f["cl"].to_numpy()
    aggr = np.zeros(n, bool)
    cons = np.zeros(n, bool)
    lx_a = np.full(n, np.nan)
    lx_c = np.full(n, np.nan)
    brk_i, brk_lvl, lx = -999, np.nan, np.nan
    last_a = last_c = -999
    cons_arm = False
    for t in range(121, n):
        if l[t] < prior20[t]:
            if t - brk_i > 4 or np.isnan(lx):
                brk_lvl, lx = prior20[t], l[t]
            lx = min(lx, l[t])
            brk_i = t
            cons_arm = True
        elif t - brk_i <= 10 and not np.isnan(lx):
            if l[t] < lx:
                cons_arm = False
        if t - brk_i > 10:
            cons_arm = False
        deep = dd[t] >= 0.30
        if deep and t - brk_i <= 4 and c[t] > brk_lvl and cl[t] >= 0.6 and c[t] > o[t] and t - last_a >= cooldown:
            aggr[t] = True
            lx_a[t] = lx
            last_a = t
        if deep and cons_arm and t - brk_i <= 10 and c[t] > ma20[t] and t - last_c >= cooldown:
            cons[t] = True
            lx_c[t] = lx
            last_c = t
            cons_arm = False
    return pd.DataFrame({"aggr": aggr, "cons": cons, "lx_aggr": lx_a, "lx_cons": lx_c}, index=df.index)


# ---------------------------------------------------------------------- evaluation

COST = 0.0016  # round trip: commission ~2x0.025% + stamp 0.05% (sell) + slippage ~0.06%
HORIZONS = (5, 10, 20, 40, 60)


def limit_pct(sym: str) -> float:
    return 0.195 if sym.startswith("30") else 0.095


def fwd_returns(df: pd.DataFrame, mask: pd.Series, sym: str, idx_ser: pd.Series | None = None) -> list[dict]:
    """Forward returns from next open; x{h} = excess over the equal-weight universe index (close-based)."""
    o, c = df["open"].to_numpy(), df["close"].to_numpy()
    I = idx_ser.reindex(df.index).ffill().to_numpy() if idx_ser is not None else None
    idx = np.flatnonzero(mask.to_numpy())
    rows = []
    lim = limit_pct(sym)
    for i in idx:
        e = i + 1
        if e >= len(o):
            continue
        if o[e] >= c[i] * (1 + lim):  # opens limit-up: cannot buy
            continue
        r = {"sym": sym, "date": df.index[i], "entry": o[e]}
        for hz in HORIZONS:
            j = e + hz - 1
            r[f"r{hz}"] = (c[j] / o[e] - 1 - COST) if j < len(c) else np.nan
            if I is not None:
                r[f"x{hz}"] = (r[f"r{hz}"] - (I[j] / I[i] - 1)) if j < len(c) else np.nan
        rows.append(r)
    return rows


def simulate(df: pd.DataFrame, f: pd.DataFrame, sig: pd.Series, lx: pd.Series, sym: str,
             time_stop: int = 40, max_risk: float = 0.12) -> list[dict]:
    """One position at a time per stock. Entry next open; stop = Lx - 0.2 ATR (close-based, exit next open);
    time stop after `time_stop` bars unless trade reached +1R; chandelier 3*ATR after +2R."""
    o, h, l, c = (df[x].to_numpy() for x in ("open", "high", "low", "close"))
    a = f["atr"].to_numpy()
    s = sig.to_numpy()
    lxs = lx.to_numpy()
    lim = limit_pct(sym)
    trades = []
    t = 0
    n = len(c)
    while t < n - 2:
        if not s[t]:
            t += 1
            continue
        e = t + 1
        if o[e] >= c[t] * (1 + lim):
            t += 1
            continue
        entry = o[e]
        stop = lxs[t] - 0.2 * a[t]
        risk = entry - stop
        if not (risk > 0) or risk / entry > max_risk:
            t += 1
            continue
        hi_close, reached1r, trail = entry, False, -np.inf
        exit_px, exit_i, why = None, None, None
        for j in range(e, n):
            if j > e and c[j - 1] < max(stop, trail):  # signal on prior close, act at this open (T+1 safe)
                exit_px, exit_i, why = o[j], j, "stop" if c[j - 1] < stop else "trail"
                break
            hi_close = max(hi_close, h[j])
            if c[j] >= entry + risk:
                reached1r = True
            if c[j] >= entry + 2 * risk:
                trail = max(trail, hi_close - 3 * a[j])
            if j - e + 1 >= time_stop and not reached1r:
                exit_px, exit_i, why = c[j], j, "time"
                break
            if j - e + 1 >= 250:
                exit_px, exit_i, why = c[j], j, "max"
                break
        if exit_px is None:
            exit_px, exit_i, why = c[-1], n - 1, "open"
        ret = exit_px / entry - 1 - COST
        trades.append({"sym": sym, "date": df.index[t], "ret": ret, "R": (exit_px - entry) / risk,
                       "bars": exit_i - e + 1, "why": why, "risk_pct": risk / entry})
        t = exit_i + 1
    return trades


def summarize(rows: list[dict], col: str) -> dict:
    d = pd.DataFrame(rows)
    if d.empty or col not in d:
        return {"n": 0}
    x = d[col].dropna()
    if x.empty:
        return {"n": 0}
    by_date = d.dropna(subset=[col]).groupby("date")[col].mean()
    se = by_date.std(ddof=1) / math.sqrt(len(by_date)) if len(by_date) > 1 else np.nan
    return {"n": int(len(x)), "dates": int(len(by_date)), "mean": x.mean(), "median": x.median(),
            "win": (x > 0).mean(), "date_mean": by_date.mean(), "t_date": by_date.mean() / se if se and se > 0 else np.nan}


def cmd_null(a=None):
    rng = np.random.default_rng(0)
    N, K, M = 120, 6, 30
    b = rng.standard_normal((20000, N))
    b -= b.mean(axis=1, keepdims=True)
    p = np.abs(np.fft.rfft(b, axis=1)) ** 2
    E = 10 * np.log10(p[:, 1:K + 1].mean(1) / p[:, K + 1:M + 1].mean(1))
    Fs = (rng.chisquare(2 * K, 200000) / (2 * K)) / (rng.chisquare(2 * (M - K), 200000) / (2 * (M - K)))
    Fdb = 10 * np.log10(Fs)
    out = {}
    for q in (0.5, 0.9, 0.95, 0.99):
        out[q] = (float(np.quantile(E, q)), float(np.quantile(Fdb, q)))
        print(f"q{q:.2f}: simulated echo {out[q][0]:+.2f} dB | F({2*K},{2*(M-K)}) {out[q][1]:+.2f} dB")
    return out


def cmd_study(a):
    files = sorted(x for x in os.listdir(a.cache) if x.endswith(".csv"))
    fw = {k: [] for k in ("all_deep", "F_aggr", "F_cons", "F_aggr+frog", "F_aggr+latent", "F_cons+frog",
                          "radar_ignite", "radar_ignite+deep", "latent85", "deep+gene3", "F_cons+gene3",
                          "F_aggr+latent+gene3", "danyang", "danyang+frog")}
    tr = {"F_aggr": [], "F_cons": [], "F_aggr+frog": [], "F_cons+frog": [], "F_cons+gene3": [], "danyang": []}
    echo_stats = []
    hist_check = {}
    data = {}
    for fn in files:
        df = load(os.path.join(a.cache, fn))
        df = df[df.index >= pd.Timestamp("2015-01-01")]
        if len(df) >= 400:
            data[fn[:-4]] = df
    rets = pd.DataFrame({k: v["close"].pct_change() for k, v in data.items()})
    rets = rets.clip(-0.21, 0.21)
    ew = rets.mean(axis=1, skipna=True).where(rets.count(axis=1) >= 20, 0.0).fillna(0.0)
    idx_ser = (1 + ew).cumprod()
    for sym, df in data.items():
        f = features(df)
        s = f_signals(df, f)
        lf = limit_features(df, sym)
        gene3 = lf["gene"] >= 3
        echo_stats.append(f["echo"].dropna().to_numpy())
        deep = (f["dd120"] >= 0.30)
        # baseline: every 10th deep day to limit overlap
        base = deep & (np.arange(len(df)) % 10 == 0)
        masks = {
            "all_deep": base,
            "F_aggr": s["aggr"],
            "F_cons": s["cons"],
            "F_aggr+frog": s["aggr"] & (f["frog"] > 0),
            "F_aggr+latent": s["aggr"] & (f["latent"].rolling(10).max() >= 80),
            "F_cons+frog": s["cons"] & (f["frog"] > 0),
            "radar_ignite": f["ignite_up"],
            "radar_ignite+deep": f["ignite_up"] & (f["dd120"].rolling(20).max() >= 0.30),
            "latent85": (f["latent"] >= 80) & (f["latent"].shift() < 80),
            "deep+gene3": base & gene3,
            "F_cons+gene3": s["cons"] & gene3,
            "F_aggr+latent+gene3": s["aggr"] & (f["latent"].rolling(10).max() >= 80) & gene3,
            "danyang": lf["danyang"],
            "danyang+frog": lf["danyang"] & (f["frog"] > 0),
        }
        for k, m in masks.items():
            fw[k] += fwd_returns(df, m.fillna(False), sym, idx_ser)
        tr["F_aggr"] += simulate(df, f, s["aggr"], s["lx_aggr"], sym)
        tr["F_cons"] += simulate(df, f, s["cons"], s["lx_cons"], sym)
        tr["F_aggr+frog"] += simulate(df, f, s["aggr"] & (f["frog"] > 0), s["lx_aggr"], sym)
        tr["F_cons+frog"] += simulate(df, f, s["cons"] & (f["frog"] > 0), s["lx_cons"], sym)
        tr["F_cons+gene3"] += simulate(df, f, s["cons"] & gene3, s["lx_cons"], sym)
        tr["danyang"] += simulate(df, f, lf["danyang"], lf["lx_danyang"], sym)
        if sym in ("600186.SS", "600241.SS", "605178.SS", "001331.SZ", "600889.SS", "002165.SZ", "300844.SZ", "601086.SS"):
            sig_dates = [str(d.date()) for d in s.index[s["aggr"] | s["cons"]] if d >= pd.Timestamp("2024-06-01")]
            hist_check[sym] = sig_dates
    lines = render(fw, tr, echo_stats, hist_check, len(data))
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(lines)
    print(lines)


def render(fw, tr, echo_stats, hist_check, nfiles) -> str:
    L = []
    L.append(f"股票数：{nfiles}（随机抽样的沪深主板与创业板现存股票，2015-01 至 2026-11，Yahoo 日线，复权）\n")
    L.append("## 事件研究：信号后 N 日收益（次日开盘买入，扣 0.16% 往返成本）\n")
    L.append("`日期均值` 先按信号日期求平均再跨日期平均，`t(日期)` 用日期层面的标准误，扣除同一天大量信号扎堆带来的虚高。`超额` = 信号收益减去同期全样本等权指数收益。\n")
    L.append("| 信号 | 样本 | 日期数 | 20日均值 | 20日中位 | 20日胜率 | 20日日期均值 | t(日期) | 20日超额(日期均值) | 超额t | 60日均值 | 60日超额 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k, rows in fw.items():
        s20, s60 = summarize(rows, "r20"), summarize(rows, "r60")
        x20, x60 = summarize(rows, "x20"), summarize(rows, "x60")
        if s20.get("n", 0) == 0:
            L.append(f"| {k} | 0 | | | | | | | | | | |")
            continue
        L.append(f"| {k} | {s20['n']} | {s20['dates']} | {s20['mean']:+.2%} | {s20['median']:+.2%} | {s20['win']:.1%} | "
                 f"{s20['date_mean']:+.2%} | {s20['t_date']:.2f} | {x20.get('date_mean', np.nan):+.2%} | {x20.get('t_date', np.nan):.2f} | "
                 f"{s60.get('mean', np.nan):+.2%} | {x60.get('date_mean', np.nan):+.2%} |")
    L.append("\n### 按时间切分（20 日均值 / 胜率 / 样本）\n")
    L.append("| 信号 | 2015–2018 | 2019–2022 | 2023–2026 |")
    L.append("|---|---|---|---|")
    for k, rows in fw.items():
        d = pd.DataFrame(rows)
        if d.empty:
            continue
        d["y"] = pd.to_datetime(d["date"]).dt.year
        cells = []
        for lo, hi in ((2015, 2018), (2019, 2022), (2023, 2026)):
            x = d[(d["y"] >= lo) & (d["y"] <= hi)]["r20"].dropna()
            cells.append(f"{x.mean():+.2%} / {(x > 0).mean():.0%} / {len(x)}" if len(x) else "—")
        L.append(f"| {k} | " + " | ".join(cells) + " |")
    L.append("\n## 交易模拟（止损 = Lx − 0.2 ATR，收盘破位次日开盘走；40 日未到 +1R 时间止损；+2R 后 3 ATR 吊灯止盈）\n")
    L.append("| 规则 | 笔数 | 胜率 | 平均收益 | 中位收益 | 平均 R | 盈亏比 | 平均持有 | 止损/时间/跟踪 占比 |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for k, rows in tr.items():
        d = pd.DataFrame(rows)
        if d.empty:
            continue
        wins, losses = d[d.ret > 0].ret, d[d.ret <= 0].ret
        pf = wins.sum() / -losses.sum() if len(losses) and losses.sum() < 0 else np.nan
        why = d["why"].value_counts(normalize=True)
        L.append(f"| {k} | {len(d)} | {(d.ret > 0).mean():.1%} | {d.ret.mean():+.2%} | {d.ret.median():+.2%} | {d.R.mean():+.2f} | "
                 f"{pf:.2f} | {d.bars.mean():.0f} 日 | {why.get('stop', 0):.0%}/{why.get('time', 0):.0%}/{why.get('trail', 0):.0%} |")
    for k, rows in tr.items():
        d = pd.DataFrame(rows)
        if d.empty:
            continue
        d["y"] = pd.to_datetime(d["date"]).dt.year
        g = d.groupby("y")["ret"].agg(["count", "mean", lambda x: (x > 0).mean()])
        L.append(f"\n{k} 按年：" + "；".join(f"{y} {int(r['count'])}笔 {r['mean']:+.1%} 胜{r['<lambda_0>']:.0%}" for y, r in g.iterrows()))
    allE = np.concatenate(echo_stats) if echo_stats else np.array([])
    if allE.size:
        L.append("\n## 实体谱雷达回波：真实 A 股 vs 随机零假设\n")
        L.append("| 分位 | A 股实测 | 随机实体（模拟） |")
        L.append("|---|---|---|")
        nul = cmd_null()
        for q in (0.5, 0.9, 0.95, 0.99):
            L.append(f"| {q:.0%} | {np.quantile(allE, q):+.2f} dB | {nul[q][0]:+.2f} dB |")
        L.append(f"\n实测回波超过 3 dB 的时间占比：{(allE > 3).mean():.1%}（随机情况下约 5%）。")
    L.append("\n## 老王晒单股票上的 F 信号（2024-06 以后，供对照 B 点，不是业绩证据）\n")
    for k, v in hist_check.items():
        L.append(f"- {k}：{', '.join(v) if v else '无'}")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("fetch"); p.add_argument("--cache", required=True); p.add_argument("--n", type=int, default=400); p.add_argument("--seed", type=int, default=7)
    sp.add_parser("null")
    p = sp.add_parser("study"); p.add_argument("--cache", required=True); p.add_argument("--out", required=True)
    a = ap.parse_args()
    {"fetch": cmd_fetch, "null": cmd_null, "study": cmd_study}[a.cmd](a)


if __name__ == "__main__":
    main()

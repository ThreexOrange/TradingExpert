"""Daily-bar tests of rules read from LWAI's course outline and his published signals.

K1  关键K (impulse version): within the last 30 bars a new 20-day low was made while the 120-day
    drawdown was >= 30%; today is the first close above MA20 since that low, with a gain >= 4%
    (or limit-up) and volume >= 1.5 x its 20-day average.
B1  1B 试盘涨停回踩: after a >= 30% drawdown, the first limit-up in 60 bars is the "试盘" bar U.
    Within the next 20 bars, buy at U's close when price pulls back into [low_U, close_U]
    (limit order; if the bar opens below close_U, fill at the open). Signal date = fill date.

Usage: python3 outline_rules.py CACHE_DIR OUT.md
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lwai_lab as L


def k1_signals(df, f, sym):
    c, o, v, l = df['close'], df['open'], df['volume'], df['low']
    lim = L.limit_pct(sym)
    newlow = l < l.rolling(20).min().shift()
    deep = f['dd120'] >= 0.30
    low_evt = (newlow & deep)
    n = len(df); sig = np.zeros(n, bool); lx = np.full(n, np.nan)
    last_low_i = -999; low_px = np.nan; crossed = True
    above = (c > f['ma20']).to_numpy(); chg = (c / c.shift() - 1).to_numpy(); vr = (v / v.rolling(20).mean()).to_numpy()
    le = low_evt.to_numpy(); lo = l.to_numpy()
    for t in range(121, n):
        if le[t]:
            last_low_i, low_px, crossed = t, lo[t] if t - last_low_i > 30 or np.isnan(low_px) else min(low_px, lo[t]), False
        if t - last_low_i > 30 or crossed:
            continue
        if above[t] and not above[t - 1]:
            crossed = True
            if (chg[t] >= 0.04 or chg[t] >= lim - 0.005) and vr[t] >= 1.5:
                sig[t] = True; lx[t] = np.nanmin(lo[last_low_i:t + 1])
    return pd.Series(sig, df.index), pd.Series(lx, df.index)


def b1_trades(df, f, sym, wait=20, hold=40):
    """Returns list of fills with forward returns measured from the fill price."""
    c, o, h, l = (df[x].to_numpy() for x in ('close', 'open', 'high', 'low'))
    lim = L.limit_pct(sym)
    up = (df['close'] / df['close'].shift() - 1 >= lim - 0.005).to_numpy()
    deep = (f['dd120'].rolling(20).max() >= 0.30).to_numpy()
    rows = []; n = len(c); last_up = -999; t = 121
    while t < n:
        if up[t] and deep[t] and t - last_up > 60:
            last_up = t
            lo_u, cl_u = l[t], c[t]
            for j in range(t + 2, min(t + 1 + wait, n)):
                if c[j - 1] < lo_u:  # closed below the trial bar: setup invalid
                    break
                if l[j] <= cl_u:
                    px = min(o[j], cl_u)
                    r = {'sym': sym, 'date': df.index[j], 'entry': px}
                    for hz in (5, 10, 20, 40, 60):
                        k = j + hz - 1
                        r[f'r{hz}'] = c[k] / px - 1 - L.COST if k < n else np.nan
                    rows.append(r)
                    break
            t += 1
            continue
        if up[t]:
            last_up = t
        t += 1
    return rows


def main():
    cache, out = sys.argv[1], sys.argv[2]
    data = {}
    for fn in sorted(os.listdir(cache)):
        if fn.endswith('.csv'):
            df = L.load(os.path.join(cache, fn)); df = df[df.index >= pd.Timestamp('2015-01-01')]
            if len(df) >= 400: data[fn[:-4]] = df
    rets = pd.DataFrame({k: v['close'].pct_change() for k, v in data.items()}).clip(-0.21, 0.21)
    ew = rets.mean(axis=1).where(rets.count(axis=1) >= 20, 0.0).fillna(0.0); I = (1 + ew).cumprod()
    fw = {'K1 关键K(冲击版)': [], 'K1 + 涨停': [], 'B1 试盘涨停回踩': [], '对照: F 稳健版': []}
    tr = {'K1 关键K(冲击版)': []}
    for sym, df in data.items():
        f = L.features(df)
        k1, lx = k1_signals(df, f, sym)
        lim = L.limit_pct(sym)
        isup = (df['close'] / df['close'].shift() - 1 >= lim - 0.005)
        fw['K1 关键K(冲击版)'] += L.fwd_returns(df, k1, sym, I)
        fw['K1 + 涨停'] += L.fwd_returns(df, k1 & isup, sym, I)
        fw['对照: F 稳健版'] += L.fwd_returns(df, L.f_signals(df, f)['cons'], sym, I)
        rows = b1_trades(df, f, sym)
        Ia = I.reindex(df.index).ffill()
        for r in rows:
            i = df.index.get_loc(r['date'])
            for hz in (5, 10, 20, 40, 60):
                k = i + hz - 1
                r[f'x{hz}'] = (r[f'r{hz}'] - (Ia.iloc[k] / Ia.iloc[i - 1] - 1)) if k < len(df) else np.nan
        fw['B1 试盘涨停回踩'] += rows
        tr['K1 关键K(冲击版)'] += L.simulate(df, f, k1, lx, sym)
    lines = [f'股票数 {len(data)}，2015-01 至 2026-11，日线，次日开盘（B1 为限价回踩成交价）买入，扣 0.16% 成本。\n',
             '| 规则 | 样本 | 日期数 | 20日均值 | 20日胜率 | 20日超额(日期均值) | 超额t | 60日均值 | 60日超额 |', '|---|---|---|---|---|---|---|---|---|']
    for k, rows in fw.items():
        s20, x20, s60, x60 = (L.summarize(rows, c) for c in ('r20', 'x20', 'r60', 'x60'))
        if s20.get('n', 0) == 0:
            lines.append(f'| {k} | 0 | | | | | | | |'); continue
        lines.append(f"| {k} | {s20['n']} | {s20['dates']} | {s20['mean']:+.2%} | {s20['win']:.1%} | {x20['date_mean']:+.2%} | {x20['t_date']:.2f} | {s60['mean']:+.2%} | {x60['date_mean']:+.2%} |")
    for k, rows in tr.items():
        d = pd.DataFrame(rows)
        if d.empty: continue
        pf = d[d.ret > 0].ret.sum() / -d[d.ret <= 0].ret.sum()
        lines.append(f"\n{k} 交易模拟：{len(d)} 笔，胜率 {(d.ret > 0).mean():.1%}，平均 {d.ret.mean():+.2%}，盈亏比 {pf:.2f}，涨≥50% 占 {(d.ret >= 0.5).mean():.1%}")
    txt = '\n'.join(lines) + '\n'
    open(out, 'w', encoding='utf-8').write(txt); print(txt)


if __name__ == '__main__':
    main()

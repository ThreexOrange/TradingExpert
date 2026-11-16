"""Regime split and right-tail check for module F trades.
Usage: python3 regime_check.py CACHE_DIR   (cache filled by `lwai_lab.py fetch`)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import lwai_lab as L
cache = sys.argv[1]
data = {}
for fn in sorted(os.listdir(cache)):
    if fn.endswith('.csv'):
        df = L.load(os.path.join(cache, fn)); df = df[df.index >= pd.Timestamp('2015-01-01')]
        if len(df) >= 400: data[fn[:-4]] = df
rets = pd.DataFrame({k: v['close'].pct_change() for k, v in data.items()}).clip(-0.21, 0.21)
ew = rets.mean(axis=1).where(rets.count(axis=1) >= 20, 0.0).fillna(0.0)
I = (1 + ew).cumprod()
reg = pd.DataFrame({'above200': I > I.rolling(200).mean(), 'mom20': I / I.shift(20) - 1,
                    'breadth': (pd.DataFrame({k: v['close'] > v['close'].rolling(20).mean() for k, v in data.items()}).mean(axis=1))})
trades = {'F_aggr': [], 'F_cons': []}
for sym, df in data.items():
    f = L.features(df); s = L.f_signals(df, f)
    trades['F_aggr'] += L.simulate(df, f, s['aggr'], s['lx_aggr'], sym)
    trades['F_cons'] += L.simulate(df, f, s['cons'], s['lx_cons'], sym)
for k, rows in trades.items():
    d = pd.DataFrame(rows); d['date'] = pd.to_datetime(d['date'])
    d = d.join(reg, on='date')
    print(f'== {k}: n={len(d)} mean={d.ret.mean():+.2%} PF={d[d.ret>0].ret.sum()/-d[d.ret<=0].ret.sum():.2f}')
    for name, m in [('EW>MA200', d.above200 == True), ('EW<MA200', d.above200 == False),
                    ('breadth>=0.5', d.breadth >= 0.5), ('breadth<0.3', d.breadth < 0.3),
                    ('EW>MA200 & breadth>=0.5', (d.above200 == True) & (d.breadth >= 0.5))]:
        x = d[m]
        if len(x):
            pf = x[x.ret>0].ret.sum()/-x[x.ret<=0].ret.sum()
            print(f'   {name:26s} n={len(x):5d} win={(x.ret>0).mean():.1%} mean={x.ret.mean():+.2%} PF={pf:.2f}')
    r = d.ret
    print(f'   right tail: >=+30% {(r>=0.3).mean():.1%}  >=+50% {(r>=0.5).mean():.1%}  >=+100% {(r>=1).mean():.2%}  | top5% trades share of gross profit {r[r>=r.quantile(0.95)].sum()/r[r>0].sum():.0%}')
    print(f'   loss side: <=-10% {(r<=-0.1).mean():.1%}  worst {r.min():+.1%}  median loss {r[r<=0].median():+.1%}')

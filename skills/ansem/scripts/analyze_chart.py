#!/usr/bin/env python3
"""Point-in-time descriptive OHLCV features and SVG; not a trading backtest.

CSV: open_time,close_time,open,high,low,close,volume (ISO with timezone).
Levels JSON: [{"price":61000,"label":"support","known_at":"...+00:00"}].
python analyze_chart.py bars.csv --asof ...Z --output report.json --svg chart.svg
"""
import argparse
import csv
import json
import math
import statistics as st
from datetime import datetime, timezone
from html import escape
from pathlib import Path


def timestamp(value):
    t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if t.tzinfo is None:
        raise ValueError('All times must include a timezone')
    return t.astimezone(timezone.utc)


def number(value):
    x = float(value)
    if not math.isfinite(x):
        raise ValueError('Nonfinite data')
    return x


def read_bars(path):
    bars = []
    with open(path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        required = {'open_time', 'close_time', 'open', 'high', 'low', 'close', 'volume'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('CSV requires: ' + ','.join(sorted(required)))
        for row in reader:
            b = {k: number(row[k]) for k in ('open', 'high', 'low', 'close')}
            b['open_time'], b['close_time'] = timestamp(row['open_time']), timestamp(row['close_time'])
            b['volume'] = number(row['volume']) if row['volume'].strip() else None
            if not (0 < b['low'] <= min(b['open'], b['close']) <= max(b['open'], b['close']) <= b['high']):
                raise ValueError('Invalid positive OHLC')
            if b['open_time'] >= b['close_time'] or (b['volume'] is not None and b['volume'] < 0):
                raise ValueError('Invalid time interval or volume')
            if bars and bars[-1]['close_time'] > b['open_time']:
                raise ValueError('Unsorted, duplicate or overlapping bars')
            bars.append(b)
    if not bars:
        raise ValueError('No bars')
    return bars


def divide(a, b):
    return a / b if b else None


def features(bars, asof, window=20, atr_period=14, benchmark=None):
    if window < 2 or atr_period < 1:
        raise ValueError('window >= 2 and atr_period >= 1 required')
    closed = [b for b in bars if b['close_time'] <= asof]
    if not closed:
        raise ValueError('No completed bars before asof')
    tr, prior_close = [], None
    for b in closed:
        tr.append(max(b['high'] - b['low'], abs(b['high'] - prior_close), abs(b['low'] - prior_close))
                  if prior_close is not None else b['high'] - b['low'])
        prior_close = b['close']
    atr = None
    if len(tr) >= atr_period:
        atr = st.mean(tr[:atr_period])
        for v in tr[atr_period:]:
            atr = ((atr_period - 1) * atr + v) / atr_period
    b = closed[-1]
    prior = closed[-window-1:-1]
    enough = len(prior) == window
    upper = max(x['high'] for x in prior) if enough else None
    lower = min(x['low'] for x in prior) if enough else None
    span = b['high'] - b['low']
    closes = [x['close'] for x in closed]
    er = None
    if len(closes) >= window + 1:
        c = closes[-window-1:]
        er = divide(abs(c[-1] - c[0]), sum(abs(y-x) for x, y in zip(c, c[1:])))
    vbase = st.median([x['volume'] for x in prior]) if enough and all(x['volume'] is not None for x in prior) else None
    report = {
        'analysis_type': 'descriptive_not_backtest',
        'attribution': 'independent_extension_not_author_parameters',
        'asof_utc': asof.isoformat(), 'last_completed_bar': b['close_time'].isoformat(),
        'completed_bars': len(closed),
        'parameters': {'prior_window': window, 'atr_period': atr_period, 'atr_method': 'Wilder_seed_mean'},
        'atr': atr, 'close': b['close'], 'prior_range_upper': upper, 'prior_range_lower': lower,
        'range_position': divide(b['close']-lower, upper-lower) if enough else None,
        'range_width_atr': divide(upper-lower, atr) if enough else None,
        'breakout_atr': divide(b['close']-upper, atr) if enough else None,
        'body_fraction': divide(abs(b['close']-b['open']), span),
        'close_location': divide(b['close']-b['low'], span),
        'lower_wick_fraction': divide(min(b['open'],b['close'])-b['low'], span),
        'upper_wick_fraction': divide(b['high']-max(b['open'],b['close']), span),
        'efficiency_ratio': er,
        'relative_volume': divide(b['volume'], vbase) if b['volume'] is not None else None,
        'relative_log_return': None, 'beta': None, 'ols_intercept': None,
        'data_gaps': sum(y['open_time'] > x['close_time'] for x,y in zip(closed,closed[1:])),
        'limitations': ['No author fills or performance inferred', 'Unknown venue/session must be checked externally',
                        'Gaps may be scheduled market closures or missing bars; inspect before interpreting'],
    }
    if benchmark is not None:
        bench = [x for x in benchmark if x['close_time'] <= asof]
        keys = lambda seq: [(x['open_time'], x['close_time']) for x in seq]
        if keys(bench) != keys(closed):
            raise ValueError('Benchmark must share exact completed intervals; do not forward-fill')
        if len(closed) >= window+1:
            ac, bc = closes[-window-1:], [x['close'] for x in bench[-window-1:]]
            a = [math.log(y/x) for x,y in zip(ac,ac[1:])]
            v = [math.log(y/x) for x,y in zip(bc,bc[1:])]
            report['relative_log_return'] = math.log(ac[-1]/ac[0])-math.log(bc[-1]/bc[0])
            var = sum((x-st.mean(v))**2 for x in v)
            beta = divide(sum((x-st.mean(v))*(y-st.mean(a)) for x,y in zip(v,a)), var)
            report['beta'] = beta
            report['ols_intercept'] = st.mean(a)-beta*st.mean(v) if beta is not None else None
            report['limitations'].append('OLS describes trailing returns only; no event Alpha or causal claim')
    return report, closed


def load_levels(path, asof):
    raw = json.loads(Path(path).read_text(encoding='utf-8')) if path else []
    if not isinstance(raw, list):
        raise ValueError('Levels must be a list')
    out = []
    for entry in raw:
        price, known = number(entry['price']), timestamp(entry['known_at'])
        if price <= 0 or known > asof:
            raise ValueError('Levels require positive price and known_at <= asof')
        out.append({'price':price, 'known_at':known.isoformat(), 'label':str(entry.get('label','level'))})
    return out


def svg_chart(bars, asof, levels, title, log=False, count=120):
    # Wall-clock x-axis deliberately preserves overnight/weekend gaps.
    if count < 1:
        raise ValueError('chart-bars must be positive')
    bars = bars[-count:]
    W,H,left,right,top,bottom = 1120,620,85,1040,70,535
    transform = math.log if log else lambda x:x
    vals = [transform(x[k]) for x in bars for k in ('low','high')]
    vals += [transform(x['price']) for x in levels]
    lo,hi = min(vals),max(vals)
    pad = (hi-lo)*0.06 if hi>lo else max(abs(lo)*0.01,0.01)
    lo,hi = lo-pad,hi+pad
    start,end = bars[0]['open_time'].timestamp(),asof.timestamp()
    x = lambda t:left+(t-start)/(end-start)*(right-left)
    y = lambda p:bottom-(transform(p)-lo)/(hi-lo)*(bottom-top)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
             '<rect width="100%" height="100%" fill="#101827"/>',
             f'<text x="{left}" y="28" fill="#f1f5f9" font-size="18">{escape(title)}</text>',
             '<text x="85" y="50" fill="#94a3b8" font-size="12">Completed bars only | descriptive research | no author fills | wall-clock UTC</text>']
    for i in range(6):
        v=lo+(hi-lo)*i/5
        p=math.exp(v) if log else v
        yy=y(p)
        parts += [f'<line x1="{left}" x2="{right}" y1="{yy}" y2="{yy}" stroke="#263449"/>',
                  f'<text x="5" y="{yy+4}" fill="#cbd5e1" font-size="12">{p:.5g}</text>']
    for b in bars:
        a,c = b['open_time'].timestamp(),b['close_time'].timestamp()
        xx=x((a+c)/2); width=max(0.5,min(12,(x(c)-x(a))*0.7))
        color='#34d399' if b['close']>=b['open'] else '#fb7185'
        parts += [f'<line x1="{xx}" x2="{xx}" y1="{y(b["high"])}" y2="{y(b["low"])}" stroke="{color}"/>',
                  f'<rect x="{xx-width/2}" y="{min(y(b["open"]),y(b["close"]))}" width="{width}" height="{max(1,abs(y(b["open"])-y(b["close"])))}" fill="{color}"/>']
    for l in levels:
        yy=y(l['price']); begin=max(start,timestamp(l['known_at']).timestamp())
        parts += [f'<line x1="{x(begin)}" x2="{right}" y1="{yy}" y2="{yy}" stroke="#fbbf24" stroke-dasharray="5 4"/>',
                  f'<text x="{left+5}" y="{yy-5}" fill="#fbbf24" font-size="12">{escape(l["label"])}: {l["price"]:g}</text>']
    parts.append(f'<line x1="{right}" x2="{right}" y1="{top}" y2="{bottom}" stroke="#60a5fa" stroke-dasharray="4 3"/>')
    for i in range(4):
        t=start+(end-start)*i/3
        label=datetime.fromtimestamp(t,timezone.utc).strftime('%m-%d %H:%M')
        parts.append(f'<text x="{x(t)-35}" y="560" fill="#94a3b8" font-size="11">{label}</text>')
    parts.append(f'<text x="85" y="596" fill="#60a5fa" font-size="12">Decision cutoff: {escape(asof.isoformat())} | axis: {"log" if log else "linear"}</text></svg>')
    return '\n'.join(parts)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('csv');p.add_argument('--asof',required=True)
    p.add_argument('--window',type=int,default=20);p.add_argument('--atr-period',type=int,default=14)
    p.add_argument('--benchmark');p.add_argument('--levels');p.add_argument('--output')
    p.add_argument('--svg');p.add_argument('--log',action='store_true');p.add_argument('--chart-bars',type=int,default=120)
    p.add_argument('--title',default='Ansem research: independently reconstructed OHLCV')
    args=p.parse_args()
    try:
        asof=timestamp(args.asof);bars=read_bars(args.csv)
        report,closed=features(bars,asof,args.window,args.atr_period,read_bars(args.benchmark) if args.benchmark else None)
        levels=load_levels(args.levels,asof);report['levels']=levels
        if levels and report['atr']:
            report['level_metrics']=[dict(l,close_distance_atr=(closed[-1]['close']-l['price'])/report['atr'],
                                           low_distance_atr=(closed[-1]['low']-l['price'])/report['atr']) for l in levels]
        output=json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
        if args.output:Path(args.output).write_text(output,encoding='utf-8')
        else:print(output,end='')
        if args.svg:Path(args.svg).write_text(svg_chart(closed,asof,levels,args.title,args.log,args.chart_bars),encoding='utf-8')
    except (ValueError,KeyError,OSError) as exc:
        p.error(str(exc))


if __name__ == '__main__':
    main()

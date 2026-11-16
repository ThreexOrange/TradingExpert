"""Turn a decoded TradingView published-chart snapshot into CSVs: OHLCV + each study's plotted values."""
import json, sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from find_metainfo import get_metainfo
snap, outdir, tag, html = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
o = json.load(open(snap, encoding='utf-8'))
os.makedirs(outdir, exist_ok=True)
main = None; studies = []
for pane in o['charts'][0]['panes']:
    for s in pane['sources']:
        if s['type'] == 'MainSeries': main = s
        elif s['type'] == 'Study' or (s['type'].startswith('study_') and 'RollDates' not in s['type']):
            studies.append(s)
bars = {r['index']: r['value'] for r in main['bars']['data']}
sym = main['state'].get('symbol'); itv = main['state'].get('interval')
summary = {'symbol': sym, 'interval': itv, 'bars': len(bars), 'studies': []}
for s in studies:
    if 'data' not in s or 'data' not in s.get('data', {}):
        summary['studies'].append({'id': s['id'], 'name': s['type'], 'rows': 0, 'plots': 0, 'graphics': {}, 'csv': None, 'note': 'no data in snapshot'}); continue
    mi = s.get('metaInfo') or {}
    if isinstance(mi, str):
        part = s['state'].get('scriptIdPart') or mi.split('$')[-1].split('@')[0]
        mi = get_metainfo(html, part) or {}
    plots = mi.get('plots', [])
    styles = mi.get('styles', {}) or {}
    names = []
    for p in plots:
        pid = p['id']; t = p.get('type')
        title = (styles.get(pid) or {}).get('title') or pid
        if t not in ('line', 'shapes', 'chars', 'arrows', 'bar_colorer', 'bg_colorer', 'colorer', 'data_offset', 'ohlc_open', 'ohlc_high', 'ohlc_low', 'ohlc_close', 'ohlc_colorer', 'alertcondition', 'dataoffset'):
            pass
        names.append(f"{title}|{t}|{pid}")
    rows = s['data']['data']
    sname = mi.get('shortDescription') or mi.get('description') or s['id']
    fn = os.path.join(outdir, f"{tag}_{s['id']}.csv")
    with open(fn, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['index', 'time', 'open', 'high', 'low', 'close', 'volume'] + names)
        for r in rows:
            v = r['value']; b = bars.get(r['index'], [None] * 6)
            w.writerow([r['index'], v[0]] + list(b[1:6]) + list(v[1:]))
    g = s['data'].get('graphics', {})
    json.dump(g, open(os.path.join(outdir, f"{tag}_{s['id']}_graphics.json"), 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump({'inputs': s['state'].get('inputs'), 'metaInfo_inputs': mi.get('inputs'), 'plots': names}, open(os.path.join(outdir, f"{tag}_{s['id']}_meta.json"), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    summary['studies'].append({'id': s['id'], 'name': sname, 'rows': len(rows), 'plots': len(names), 'graphics': {k: (len(v) if hasattr(v, '__len__') else v) for k, v in g.items()}, 'csv': fn})
print(json.dumps(summary, ensure_ascii=False, indent=1))

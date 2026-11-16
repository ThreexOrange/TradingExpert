"""Decode the published chart snapshot embedded in a TradingView script page into JSON."""
import re, json, sys
src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
best = None
for m in re.finditer(r'"((?:[^"\\]|\\.){20000,})"', s):
    lit = m.group(1)
    if '\\"bars\\"' not in lit and '"bars"' not in lit:
        continue
    try:
        txt = json.loads('"' + lit + '"')
    except Exception:
        continue
    if best is None or len(txt) > len(best):
        best = txt
obj = json.loads(best)
json.dump(obj, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
def walk(o, path='', depth=0):
    if depth > 6: return
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)):
                n = len(v)
                print('  ' * depth + f'{k}: {type(v).__name__}[{n}]')
                if k not in ('data', 'inputs', 'styles', 'palettes', 'graphics', 'plots', 'defaults', 'filledAreas', 'bands'):
                    walk(v, path + '/' + k, depth + 1)
            elif k in ('type', 'id', 'shortDescription', 'description', 'symbol', 'interval', 'name'):
                print('  ' * depth + f'{k} = {str(v)[:80]}')
    elif isinstance(o, list):
        for i, v in enumerate(o[:6]):
            print('  ' * depth + f'[{i}]')
            walk(v, path + f'[{i}]', depth + 1)
walk(obj)

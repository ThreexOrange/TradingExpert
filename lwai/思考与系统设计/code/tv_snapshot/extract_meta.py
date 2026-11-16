import re, json, sys, html
src = sys.argv[1]
s = open(src, encoding='utf-8').read()
# find JSON string literal(s) that contain metaInfo; decode escape levels by json.loads on enclosing string
def find_arrays(text, key):
    out = []
    for m in re.finditer(re.escape('"%s":[' % key), text):
        i = m.end() - 1
        depth = 0; j = i; instr = False; esc = False
        while j < len(text):
            c = text[j]
            if instr:
                if esc: esc = False
                elif c == '\\': esc = True
                elif c == '"': instr = False
            else:
                if c == '"': instr = True
                elif c == '[': depth += 1
                elif c == ']':
                    depth -= 1
                    if depth == 0: break
            j += 1
        try:
            out.append(json.loads(text[i:j+1]))
        except Exception as e:
            pass
    return out
def find_objs(text, key):
    out = []
    for m in re.finditer(re.escape('"%s":{' % key), text):
        i = m.end() - 1
        depth = 0; j = i; instr = False; esc = False
        while j < len(text):
            c = text[j]
            if instr:
                if esc: esc = False
                elif c == '\\': esc = True
                elif c == '"': instr = False
            else:
                if c == '"': instr = True
                elif c == '{': depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0: break
            j += 1
        try:
            out.append(json.loads(text[i:j+1]))
        except Exception:
            pass
    return out
# collect decoded layers: raw, and decoded JSON string literals that are long
layers = [s]
for m in re.finditer(r'"((?:[^"\\]|\\.){5000,})"', s):
    try:
        layers.append(json.loads('"' + m.group(1) + '"'))
    except Exception:
        pass
more = []
for L in layers[1:]:
    for m in re.finditer(r'"((?:[^"\\]|\\.){5000,})"', L):
        try: more.append(json.loads('"' + m.group(1) + '"'))
        except Exception: pass
layers += more
best_inputs = []
styles = {}
desc = ''
for L in layers:
    for arr in find_arrays(L, 'inputs'):
        if isinstance(arr, list) and arr and isinstance(arr[0], dict) and 'defval' in arr[0]:
            if len(arr) > len(best_inputs): best_inputs = arr
    for o in find_objs(L, 'styles'):
        for k, v in o.items():
            if isinstance(v, dict) and ('title' in v or 'text' in v):
                styles[k] = v
    for mm in re.finditer(r'"shortDescription":"([^"]*)"', L):
        desc = mm.group(1)
print('SCRIPT:', desc)
grp = None
for it in best_inputs:
    if it.get('isHidden') or it.get('id','').startswith('__'): continue
    g = it.get('group', '')
    if g != grp:
        print('\n  [%s]' % g); grp = g
    tip = (it.get('tooltip') or '').replace('\n', ' ')
    opts = it.get('options')
    print('   - %s = %r%s%s' % (it.get('name'), it.get('defval'), ('  options=%s' % opts) if opts else '', ('  // ' + tip) if tip else ''))
print('\n  ALERTS/PLOTS:')
for k, v in styles.items():
    t = v.get('title'); x = v.get('text')
    if x or (t and not t.startswith('Plot')):
        print('   -', t, '|', (x or '').replace('\n',' '))

"""Find full metaInfo objects (plots + styles titles) embedded in a TradingView script page."""
import re, json, sys
def layers(s):
    L = [s]
    for _ in range(2):
        nxt = []
        for t in L[-1:] if False else L:
            for m in re.finditer(r'"((?:[^"\\]|\\.){5000,})"', t):
                try: nxt.append(json.loads('"' + m.group(1) + '"'))
                except Exception: pass
        L += nxt
    return L
def objects_with(text, needle):
    out = []
    for m in re.finditer(re.escape(needle), text):
        # walk back to find enclosing '{' that parses
        start = m.start()
        depth = 0
        i = start
        while i > 0:
            c = text[i]
            if c == '}': depth += 1
            elif c == '{':
                if depth == 0:
                    # try to parse from i
                    d = 0; j = i; instr = False; esc = False
                    while j < len(text):
                        ch = text[j]
                        if instr:
                            if esc: esc = False
                            elif ch == '\\': esc = True
                            elif ch == '"': instr = False
                        else:
                            if ch == '"': instr = True
                            elif ch == '{': d += 1
                            elif ch == '}':
                                d -= 1
                                if d == 0: break
                        j += 1
                    try:
                        ob = json.loads(text[i:j + 1])
                        if 'plots' in ob and 'styles' in ob:
                            out.append(ob); break
                    except Exception:
                        pass
                else:
                    depth -= 1
            i -= 1
    return out
def get_metainfo(html_path, script_part):
    s = open(html_path, encoding='utf-8').read()
    for L in layers(s):
        obs = objects_with(L, '"scriptIdPart":"%s"' % script_part)
        if obs:
            return max(obs, key=lambda o: len(o.get('plots', [])))
    return None
if __name__ == '__main__':
    mi = get_metainfo(sys.argv[1], sys.argv[2])
    if mi is None: print('not found'); sys.exit(1)
    for p in mi['plots']:
        print(p['id'], p.get('type'), (mi['styles'].get(p['id']) or {}).get('title'), p.get('target', ''))

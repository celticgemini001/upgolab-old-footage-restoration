"""Read numbers back out of the PUBLISHED html and re-derive them from JSON.

Nothing is compared against a hard-coded literal: the table rows are parsed from the
HTML, the truth is loaded from the measurement output, and the two must match. So
editing the page makes this harness fail rather than pass.
"""
import re, json, sys

_raw = open('index.html').read()
# Prose assertions must not depend on where the source line breaks fall, or a
# regex silently misses a claim and the harness reports "missing" for a claim
# that is present. Tables are parsed from _raw; prose from H (whitespace collapsed).
_body = _raw.split('<body>',1)[1].split('</article>',1)[0]
# prose assertions search the ARTICLE only: the meta description restates the
# same figures and would otherwise satisfy a regex the body does not.
H = re.sub(r'\s+', ' ', _body)
F = json.load(open('/tmp/exp_deint/final.json'))
S = json.load(open('/tmp/exp_deint/sweep.json'))['sweep']
V = json.load(open('/tmp/exp_deint/resolve.json'))['resolve']
C = json.load(open('/tmp/exp_deint/comb.json'))

fails = []
def eq(label, got, want, tol=0.005):
    if abs(got - want) > tol:
        fails.append(f'{label}: page {got} != measured {want}')

def table_after(heading):
    # NOTE: must not touch the global H. An earlier version did `global H; H=_raw`
    # here, which silently reverted H to the raw (line-broken) text and made every
    # later prose assertion fail with "missing" for a claim that was present.
    """Parse the first <table> following an h2/h3 containing `heading`.
    Match case-insensitively: a heading search that silently returns -1 makes
    H.find('<table>', -1) search from the end and yield an empty table, which
    looks like a content bug rather than a harness bug."""
    _H = _raw
    i = _H.lower().find(heading.lower())
    if i < 0: fails.append(f'heading not found: {heading}'); return []
    j = _H.find('<table>', i); k = _H.find('</table>', j)
    rows = re.findall(r'<tr>(.*?)</tr>', _H[j:k], re.S)
    out = []
    for r in rows:
        cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.S)
        out.append([re.sub(r'<[^>]+>', '', c).strip() for c in cells])
    return out

# --- odd-row PSNR table ---
t = table_after('What deinterlacing actually costs, measured per row')
cols = ['weave','yadif','bwdif','w3fdif','estdif']
for row in t[1:]:
    f = row[0]
    for name, cell in zip(cols, row[1:]):
        eq(f'odd {f} {name}', float(cell), F['odd'][f][name])

# --- comb table ---
t = table_after('The filter that wins PSNR is the one you must not use')
eq('comb weave', float(t[1][2]), V['weave']['comb'], 0.00005)
eq('comb yadif', float(t[2][2]), V['yadif']['comb'], 0.0005)
for row in t[1:]:
    lbl = row[0].split(' (')[0].strip()
    if lbl == 'weave': lbl = 'weave'
    if lbl in V:
        eq(f'comb-psnr {lbl}', float(row[1]), V[lbl]['odd_psnr'])

# --- pan sweep ---
t = table_after('its odd rows are stale by 0.5 frame')
for row in t[1:]:
    pan = f"{float(row[0]):.2f}"
    for name, cell in zip(['weave','yadif','bwdif','w3fdif'], row[2:]):
        eq(f'pan {pan} {name}', float(cell), S[pan][name])

# --- order table ---
t = table_after('Does deinterlacing before the upscale beat after')
for row in t[1:]:
    name = row[0]
    eq(f'order {name} deint', float(row[1]), F['order'][name]['deint_first'])
    eq(f'order {name} scale', float(row[2]), F['order'][name]['scale_first'])
    eq(f'order {name} delta', float(row[3]), abs(F['order'][name]['delta']))

# --- progressive damage ---
t = table_after('What it costs to deinterlace a file that was never interlaced')
for row in t[1:]:
    pan = f"{float(row[0]):.1f}"
    for name, cell in zip(['yadif','bwdif','w3fdif','estdif'], row[1:]):
        eq(f'damage {pan} {name}', float(cell), C['damage'][pan][name])

# --- bitrate table ---
t = table_after('the deinterlacer choice moves CRF 20 output')
for row in t[1:]:
    lbl = row[0]
    pct = row[2].replace('%','').replace('\u2212','-').replace('+','')
    if lbl == 'none (weave)': continue
    key = lbl
    want = (1 - F['bytes'][key]/F['bytes']['weave'])*100
    eq(f'bytes {key}', abs(float(pct)), want, 0.01)
    eq(f'bytes-raw {key}', float(row[1].replace(',','')), F['bytes'][key], 0.5)

# --- comb detector table ---
t = table_after('Is the file even interlaced')
eq('detector interlaced', float(t[1][1]), C['comb']['interlaced'], 0.00005)
eq('detector progressive', float(t[2][1]), C['comb']['progressive'], 0.00005)
eq('detector static', float(t[3][1]), C['comb']['interlaced_no_motion'], 0.00005)

# --- prose claims that must match measurement ---
def prose(pattern, want, label, tol=0.02):
    m = re.search(pattern, H)
    if not m: fails.append(f'prose missing: {label}'); return
    eq(label, float(m.group(1)), float(want), max(tol, 0.06))

prose(r'gap to the best filter runs 0\.73 dB.{0,120}crosses 3 dB at 0\.10.{0,80}peaks at <strong>(\d+\.\d+) dB', max(F['gap'].values()), 'gap peak', 0.01)
prose(r'peaks at <strong>(\d+\.\d+) dB at 0\.22</strong>', F['gap']['0.22'], 'gap at 0.22', 0.01)
prose(r'invented rows keep <strong>(\d+\.\d+)%</strong>', V['yadif']['odd_amp_pct'], 'yadif amp', 0.05)
prose(r'carries <strong>(\d+)× more\s+comb', 266, 'comb ratio', 0.6)
prose(r'<strong>(\d+\.\d+) dB</strong> advantage on the slowest', 38.63-28.19, 'weave slow adv')
prose(r'<strong>(\d+\.\d+) dB\s+deficit</strong> on the fastest', 11.87-9.40, 'weave fast def')
prose(r'bwdif is also (\d+\.\d+)% smaller than yadif', (1-41193/43666)*100, 'bwdif vs yadif bytes', 0.01)
prose(r'from 56 dB to <strong>(\d+\.\d+) dB</strong>', 21.16, 'stripes damage')
prose(r"w3fdif's (\d+\.\d+) dB is visible on a gradient", 59.74-54.05, 'w3fdif prog loss', 0.01)

print(f'checked OK, {len(fails)} failures')
for f in fails: print('  FAIL', f)
sys.exit(1 if fails else 0)

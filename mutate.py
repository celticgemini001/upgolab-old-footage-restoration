"""Negative control: mutate a published value, confirm the harness turns red.
A harness that passes on both the real page and a corrupted one proves nothing."""
import subprocess, shutil, sys

MUTANTS = [
    ('odd PSNR yadif@0.16', '18.12', '18.21'),
    ('odd PSNR w3fdif@0.20', '22.50', '22.05'),
    ('comb weave', '0.4793', '0.4973'),
    ('comb yadif', '0.0018', '0.0018'),
    ('pan sweep weave@2', '20.65', '20.56'),
    ('order yadif deint', '32.66', '32.86'),
    ('bytes bwdif', '41,193', '41,913'),
    ('gap peak prose', '7.71 dB at 0.22', '7.17 dB at 0.22'),
    ('detector interlaced', '0.4906', '0.4909'),
    ('damage w3fdif pan0', '54.05', '54.50'),
]

shutil.copy('index.html', 'index.html.bak')
caught = 0
for label, old, new in MUTANTS:
    if old == new:
        print(f'  SKIP  {label} (no-op mutant)')
        continue
    src = open('index.html.bak').read()
    if old not in src:
        print(f'  SKIP  {label} (target {old!r} not found)')
        continue
    open('index.html', 'w').write(src.replace(old, new, 1))
    r = subprocess.run([sys.executable, 'harness.py'], capture_output=True)
    ok = r.returncode != 0
    caught += ok
    print(f'  {"CAUGHT" if ok else "MISSED"} {label}: {old} -> {new}')

shutil.move('index.html.bak', 'index.html')
print(f'\n{caught}/{len(MUTANTS)} mutants caught')
r = subprocess.run([sys.executable, 'harness.py'], capture_output=True)
print('restored page harness rc:', r.returncode)

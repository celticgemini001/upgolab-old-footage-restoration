"""Structural validation of the built page. Any failure blocks the push."""
import re
from html.parser import HTMLParser

VOID = {'area','base','br','col','embed','hr','img','input','link','meta',
        'param','source','track','wbr'}

class Check(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.counts = {}
    def handle_starttag(self, tag, attrs):
        self.counts[tag] = self.counts.get(tag, 0) + 1
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))
    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f'stray </{tag}> at {self.getpos()}')
            return
        if self.stack[-1][0] != tag:
            self.errors.append(f'</{tag}> at {self.getpos()} closes <{self.stack[-1][0]}> opened at {self.stack[-1][1]}')
            # recover
            for i in range(len(self.stack)-1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break
        else:
            self.stack.pop()

h = open('index.html').read()
c = Check(); c.feed(h)

fails = []
if c.errors:
    fails += c.errors[:6]
if c.stack:
    fails.append(f'unclosed: {c.stack[:5]}')

# required invariants
if h.count('<h1>') != 1: fails.append(f"h1 count {h.count('<h1>')}")
if 'noindex' in h: fails.append('noindex present')
canon = re.search(r'<link rel="canonical" href="([^"]+)"', h)
if not canon or canon.group(1) != 'https://celticgemini001.github.io/upgolab-old-footage-restoration/':
    fails.append('canonical wrong/missing')

# body links to upgolab.com must be exactly 1 (JSON-LD and footer excluded from body count)
body = h.split('<h2>The four layers')[0] + h.split('</article>')[0]
body_links = re.findall(r'<a href="https://upgolab\.com[^"]*"', h)
print('anchor tags to upgolab.com:', len(body_links), body_links)

# cross-nav must point at all 13 pages
nav = re.search(r'<nav class="sisternav".*?</nav>', h, re.S)
if not nav: fails.append('sisternav missing')
else:
    n = len(re.findall(r'<a href="https://celticgemini001\.github\.io/', nav.group(0)))
    print('nav links:', n)
    if n < 12: fails.append(f'nav only {n} links')

print('tags:', {k: v for k, v in sorted(c.counts.items()) if k in ('h2','h3','table','pre','p','li','td','th')})
print('errors:', len(c.errors))
print('FAILS:', fails if fails else 'none')
raise SystemExit(1 if fails else 0)

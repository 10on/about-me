#!/usr/bin/env python3
"""Build script: converts content/*.md → injects into index.html between BUILD markers.
Usage: python3 build.py
"""
import re
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    print("Run: pip3 install markdown", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent
CONTENT = ROOT / 'content'

# slug → target html file
TARGETS = {
    'retro': ROOT / 'retro.html',
    'diy':   ROOT / 'diy.html',
}

def main():
    md = markdown.Markdown()

    for slug, target in TARGETS.items():
        src = CONTENT / f'{slug}.md'
        if not src.exists():
            print(f'  skip: content/{slug}.md not found')
            continue
        if not target.exists():
            print(f'  skip: {target.name} not found')
            continue

        md.reset()
        rendered = md.convert(src.read_text(encoding='utf-8'))
        block = f'<div class="md-content">\n{rendered}\n</div>'

        start = f'<!-- BUILD:{slug} -->'
        end   = f'<!-- /BUILD:{slug} -->'
        pattern = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.DOTALL)

        html = target.read_text(encoding='utf-8')
        html, n = pattern.subn(f'{start}\n{block}\n{end}', html)
        if n == 0:
            print(f'  warning: marker BUILD:{slug} not found in {target.name}')
        else:
            target.write_text(html, encoding='utf-8')
            print(f'  built: {slug} → {target.name}')

    print('done.')

if __name__ == '__main__':
    main()

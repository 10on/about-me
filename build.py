#!/usr/bin/env python3
"""Build script: converts content/*.md → injects into target HTML between BUILD markers.
Also converts content/articles/*.md (with front-matter) into standalone articles/<slug>.html
pages, plus injects list/preview blocks into articles.html and index.html.
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
ARTICLES_SRC = CONTENT / 'articles'
ARTICLES_OUT = ROOT / 'articles'

# slug → target html file, content injected as a single markdown block
TARGETS = {
    'retro': ROOT / 'retro.html',
    'diy':   ROOT / 'diy.html',
}

ARTICLE_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — дэнчик</title>
    <script>try{{var t=localStorage.getItem('denchik-theme');if(t)document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}</script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <header>
        <div class="header-top">
            <div>
                <a href="../index.html" class="logo">дэнчик</a>
                <div class="tagline">бэкенд · лего · ретро · самоделки</div>
            </div>
            <div class="header-actions">
                <button id="theme-toggle" class="theme-toggle" title="тема">☾</button>
            </div>
        </div>
        <nav>
            <a href="../notes.html">заметки</a>
            <a href="../articles.html" class="active">статьи</a>
            <a href="../lego.html">лего</a>
            <a href="../retro.html">ретро</a>
            <a href="../diy.html">самоделки</a>
            <a href="../games.html">игры</a>
            <a href="../about.html">обо мне</a>
        </nav>
    </header>

    <main>
        <div class="container" style="padding-top: 2rem; padding-bottom: 1rem; max-width: 640px;">
            <a href="../articles.html" class="back-link">← все статьи</a>
            <div class="article-header">
                <span class="article-tag">{tag_text}</span><span>{date}</span><span>· {read}</span>
            </div>
            <h1 class="article-title">{title}</h1>
            <div class="article-body">
{body}
            </div>
        </div>
    </main>

    <footer>
        <div class="footer-links">
            <a href="https://www.youtube.com/@DenchikBricks" target="_blank" rel="noopener">youtube</a>
            <a href="http://t.me/denchik_bricks" target="_blank" rel="noopener">telegram</a>
            <a href="https://rebrickable.com/users/10on/lego/" target="_blank" rel="noopener">rebrickable</a>
            <a href="https://www.linkedin.com/in/d-push/" target="_blank" rel="noopener">linkedin</a>
            <a href="mailto:igoo10on@gmail.com">почта</a>
        </div>
        <div class="footer-meta">дэнчик — <span id="year"></span> · сделано руками · без облака и трекеров</div>
    </footer>

    <script>
        document.getElementById('year').textContent = new Date().getFullYear();
        var themeBtn = document.getElementById('theme-toggle');
        function syncThemeLabel() {{ themeBtn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀︎' : '☾'; }}
        syncThemeLabel();
        themeBtn.addEventListener('click', function () {{
            var next = document.documentElement.getAttribute('data-theme') === 'dark' ? '' : 'dark';
            if (next) document.documentElement.setAttribute('data-theme', next); else document.documentElement.removeAttribute('data-theme');
            syncThemeLabel();
            try {{ localStorage.setItem('denchik-theme', next); }} catch (e) {{}}
        }});
    </script>
</body>
</html>
"""


def parse_front_matter(text):
    """Split leading `---\\nkey: value\\n---` block from the markdown body."""
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', text, re.DOTALL)
    if not m:
        return {}, text
    raw, body = m.groups()
    meta = {}
    for line in raw.splitlines():
        if ':' not in line:
            continue
        key, _, value = line.partition(':')
        meta[key.strip()] = value.strip()
    return meta, body


def load_articles():
    """Read content/articles/*.md, newest first (filenames prefixed YYYY-MM-DD-slug.md)."""
    if not ARTICLES_SRC.exists():
        return []
    articles = []
    for path in sorted(ARTICLES_SRC.glob('*.md'), reverse=True):
        meta, body = parse_front_matter(path.read_text(encoding='utf-8'))
        slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', path.stem)
        tags = [t.strip() for t in meta.get('tags', '').split(',') if t.strip()]
        articles.append({
            'slug': slug,
            'title': meta.get('title', slug),
            'date': meta.get('date', ''),
            'read': meta.get('read', ''),
            'excerpt': meta.get('excerpt', ''),
            'tags': tags,
            'body': body,
        })
    return articles


def render_article_page(md, article):
    md.reset()
    body_html = md.convert(article['body'])
    tag_text = ' '.join(f'#{t}' for t in article['tags'])
    html = ARTICLE_TEMPLATE.format(
        title=article['title'], tag_text=tag_text, date=article['date'],
        read=article['read'], body=body_html,
    )
    ARTICLES_OUT.mkdir(exist_ok=True)
    out_path = ARTICLES_OUT / f"{article['slug']}.html"
    out_path.write_text(html, encoding='utf-8')
    print(f"  built: articles/{article['slug']}.html")


def render_card(article, prefix=''):
    tag_text = ' '.join(f'#{t}' for t in article['tags'])
    return (
        f'<div class="article-card">'
        f'<div class="article-meta"><span class="article-tag">{tag_text}</span>'
        f'<span>{article["date"]}</span><span>· {article["read"]}</span></div>'
        f'<h3><a href="{prefix}articles/{article["slug"]}.html">{article["title"]}</a></h3>'
        f'<p>{article["excerpt"]}</p>'
        f'<a class="article-read-link" href="{prefix}articles/{article["slug"]}.html">читать →</a>'
        f'</div>'
    )


def inject(target, slug, block):
    start, end = f'<!-- BUILD:{slug} -->', f'<!-- /BUILD:{slug} -->'
    pattern = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.DOTALL)
    html = target.read_text(encoding='utf-8')
    html, n = pattern.subn(f'{start}\n{block}\n{end}', html)
    if n == 0:
        print(f'  warning: marker BUILD:{slug} not found in {target.name}')
    else:
        target.write_text(html, encoding='utf-8')
        print(f'  built: {slug} → {target.name}')


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
        inject(target, slug, block)

    articles = load_articles()
    for article in articles:
        render_article_page(md, article)

    articles_html = ROOT / 'articles.html'
    if articles_html.exists():
        block = ''.join(render_card(a) for a in articles) if articles else '<p class="empty">скоро будет...</p>'
        inject(articles_html, 'articles-list', block)

    index_html = ROOT / 'index.html'
    if index_html.exists():
        preview = articles[:3]
        block = ''.join(render_card(a) for a in preview) if preview else '<p class="empty">скоро будет...</p>'
        inject(index_html, 'articles-home', block)

    print('done.')

if __name__ == '__main__':
    main()

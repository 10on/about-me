#!/usr/bin/env python3
"""Build script: converts content/*.md → injects into target HTML between BUILD markers.
Also converts content/articles/*.md (with front-matter) into standalone articles/<slug>.html
pages, plus injects list/preview blocks into articles.html and index.html.

Bilingual: everything above also runs for the English mirror under en/. Russian sources are
content/<slug>.md, content/notes/*.md, content/articles/*.md; their English counterparts are
the same filenames with an extra .en suffix before .md (content/about.en.md,
content/notes/2026-07-22-foo.en.md, content/articles/2026-01-01-bar.en.md). An English source
is optional per-slug/per-note/per-article — anything without a matching .en.md is simply
skipped for the en/ build.

Usage: python3 build.py
"""
import html
import json
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
NOTES_SRC = CONTENT / 'notes'

SITE_URL = 'https://10on.github.io/about-me'
STATIC_PAGES = [
    '', 'notes.html', 'articles.html', 'about.html',
    'lego.html', 'retro.html', 'diy.html', 'games.html', 'projects.html',
]

NAV_LABELS = {
    'ru': {'notes': 'заметки', 'articles': 'статьи', 'lego': 'лего', 'retro': 'ретро',
           'diy': 'самоделки', 'games': 'игры', 'about': 'обо мне'},
    'en': {'notes': 'notes', 'articles': 'articles', 'lego': 'lego', 'retro': 'retro',
           'diy': 'DIY', 'games': 'games', 'about': 'about'},
}
BRAND = {'ru': 'дэнчик', 'en': 'Denchik'}
TAGLINE = {'ru': 'лего · ретро · самоделки · разработка', 'en': 'lego · retro · DIY · dev'}
STRINGS = {
    'ru': {'theme_title': 'тема', 'email': 'почта', 'all_articles': '← все статьи', 'read_more': 'читать →'},
    'en': {'theme_title': 'theme', 'email': 'email', 'all_articles': '← all articles', 'read_more': 'read →'},
}

# slug → per-language target html file, content injected as a single markdown block.
# wrapper class defaults to 'md-content'; override per-slug when the page needs different styling.
TARGETS = {
    'ru': {
        'retro': {'target': ROOT / 'retro.html'},
        'diy':   {'target': ROOT / 'diy.html'},
        'about': {'target': ROOT / 'about.html', 'class': 'bio-content'},
    },
    'en': {
        'retro': {'target': ROOT / 'en' / 'retro.html'},
        'diy':   {'target': ROOT / 'en' / 'diy.html'},
        'about': {'target': ROOT / 'en' / 'about.html', 'class': 'bio-content'},
    },
}

LANG_DIRS = {'ru': ROOT, 'en': ROOT / 'en'}


def article_template(lang):
    site_root = '../' if lang == 'ru' else '../../'
    nav = NAV_LABELS[lang]
    s = STRINGS[lang]
    return """<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} — """ + BRAND[lang] + """</title>
    <meta name="description" content="{{description}}">
    <link rel="canonical" href="{{url}}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content=\"""" + BRAND[lang] + """\">
    <meta property="og:title" content="{{title}} — """ + BRAND[lang] + """">
    <meta property="og:description" content="{{description}}">
    <meta property="og:url" content="{{url}}">
    <meta property="og:image" content="https://10on.github.io/about-me/img/persik.jpg">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:image" content="https://10on.github.io/about-me/img/persik.jpg">
    <script>try{{var t=localStorage.getItem('denchik-theme');if(t)document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}</script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href=\"""" + site_root + """style.css">
</head>
<body>
    <header>
        <div class="header-top">
            <div>
                <a href="../index.html" class="logo">""" + BRAND[lang] + """</a>
                <div class="tagline">""" + TAGLINE[lang] + """</div>
            </div>
            <div class="header-actions">
                <button id="theme-toggle" class="theme-toggle" title=\"""" + s['theme_title'] + """\">☾</button>
            </div>
        </div>
        <nav>
            <a href="../notes.html">""" + nav['notes'] + """</a>
            <a href="../articles.html" class="active">""" + nav['articles'] + """</a>
            <a href="../lego.html">""" + nav['lego'] + """</a>
            <a href="../retro.html">""" + nav['retro'] + """</a>
            <a href="../diy.html">""" + nav['diy'] + """</a>
            <a href="../games.html">""" + nav['games'] + """</a>
            <a href="../about.html">""" + nav['about'] + """</a>
        </nav>
    </header>

    <main>
        <div class="container" style="padding-top: 2rem; padding-bottom: 1rem; max-width: 640px;">
            <a href="../articles.html" class="back-link">""" + s['all_articles'] + """</a>
            <div class="article-header">
                <span class="article-tag">{{tag_text}}</span><span>{{date}}</span><span>· {{read}}</span>
            </div>
            <h1 class="article-title">{{title}}</h1>
            <div class="article-body">
{{body}}
            </div>
        </div>
    </main>

    <footer>
        <div class="footer-links">
            <a href="https://www.youtube.com/@DenchikBricks" target="_blank" rel="noopener">youtube</a>
            <a href="http://t.me/denchik_bricks" target="_blank" rel="noopener">telegram</a>
            <a href="https://rebrickable.com/users/10on/lego/" target="_blank" rel="noopener">rebrickable</a>
            <a href="https://www.linkedin.com/in/d-push/" target="_blank" rel="noopener">linkedin</a>
            <a href="mailto:igoo10on@gmail.com">""" + s['email'] + """</a>
        </div>
        <div class="footer-meta">""" + BRAND[lang] + """ — <span id="year"></span></div>
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
""".format(lang=lang)


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


def lang_files(src_dir, lang):
    """*.md files belonging to `lang`: en sources end in .en.md, ru sources don't."""
    if not src_dir.exists():
        return []
    files = sorted(src_dir.glob('*.md'), reverse=True)
    if lang == 'en':
        return [p for p in files if p.name.endswith('.en.md')]
    return [p for p in files if not p.name.endswith('.en.md')]


def slug_from_path(path, lang):
    stem = path.stem  # e.g. '2026-01-01-my-slug' or '2026-01-01-my-slug.en'
    if lang == 'en' and stem.endswith('.en'):
        stem = stem[:-3]
    return re.sub(r'^\d{4}-\d{2}-\d{2}-', '', stem)


def load_articles(lang):
    """Read content/articles/*.md for `lang`, newest first (filenames YYYY-MM-DD-slug[.en].md)."""
    articles = []
    for path in lang_files(ARTICLES_SRC, lang):
        meta, body = parse_front_matter(path.read_text(encoding='utf-8'))
        slug = slug_from_path(path, lang)
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


def render_article_page(md, article, lang, template):
    md.reset()
    body_html = md.convert(article['body'])
    tag_text = ' '.join(f'#{t}' for t in article['tags'])
    lang_root = SITE_URL if lang == 'ru' else f'{SITE_URL}/en'
    page_html = template.format(
        title=article['title'], tag_text=tag_text, date=article['date'],
        read=article['read'], body=body_html,
        description=html.escape(article['excerpt'], quote=True),
        url=f"{lang_root}/articles/{article['slug']}.html",
    )
    out_dir = LANG_DIRS[lang] / 'articles'
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{article['slug']}.html"
    out_path.write_text(page_html, encoding='utf-8')
    print(f"  built: {'en/' if lang == 'en' else ''}articles/{article['slug']}.html")


def load_notes(lang):
    """Read content/notes/*.md for `lang`, newest first (filenames YYYY-MM-DD-slug[.en].md)."""
    notes = []
    for path in lang_files(NOTES_SRC, lang):
        meta, body = parse_front_matter(path.read_text(encoding='utf-8'))
        tags = [t.strip() for t in meta.get('tags', '').split(',') if t.strip()]
        notes.append({'date': meta.get('date', ''), 'tags': tags, 'body': body.strip()})
    return notes


def render_note_text(md, body):
    """Markdown body → flat HTML string (paragraphs joined with <br><br> instead of <p>),
    since notes.json feeds a single innerHTML string per note, not a full block layout."""
    md.reset()
    rendered = md.convert(body).strip()
    rendered = re.sub(r'^<p>', '', rendered)
    rendered = re.sub(r'</p>$', '', rendered)
    return rendered.replace('</p>\n<p>', '<br><br>')


def generate_notes_json(md, notes, out_path):
    data = [
        {'date': n['date'], 'tags': n['tags'], 'text': render_note_text(md, n['body'])}
        for n in notes
    ]
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'  built: {out_path.relative_to(ROOT)}')


def render_card(article, lang, prefix=''):
    tag_text = ' '.join(f'#{t}' for t in article['tags'])
    read_more = STRINGS[lang]['read_more']
    return (
        f'<div class="article-card">'
        f'<div class="article-meta"><span class="article-tag">{tag_text}</span>'
        f'<span>{article["date"]}</span><span>· {article["read"]}</span></div>'
        f'<h3><a href="{prefix}articles/{article["slug"]}.html">{article["title"]}</a></h3>'
        f'<p>{article["excerpt"]}</p>'
        f'<a class="article-read-link" href="{prefix}articles/{article["slug"]}.html">{read_more}</a>'
        f'</div>'
    )


def inject(target, slug, block):
    start, end = f'<!-- BUILD:{slug} -->', f'<!-- /BUILD:{slug} -->'
    pattern = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.DOTALL)
    src = target.read_text(encoding='utf-8')
    src, n = pattern.subn(f'{start}\n{block}\n{end}', src)
    if n == 0:
        print(f'  warning: marker BUILD:{slug} not found in {target.name}')
    else:
        target.write_text(src, encoding='utf-8')
        print(f'  built: {slug} → {target.name}')


def generate_sitemap(articles_by_lang):
    urls = [f'{SITE_URL}/{page}' for page in STATIC_PAGES]
    urls += [f"{SITE_URL}/articles/{a['slug']}.html" for a in articles_by_lang['ru']]
    urls += [f'{SITE_URL}/en/{page}' for page in STATIC_PAGES]
    urls += [f"{SITE_URL}/en/articles/{a['slug']}.html" for a in articles_by_lang['en']]
    body = '\n'.join(
        f'  <url><loc>{u}</loc></url>' for u in urls
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'{body}\n'
        '</urlset>\n'
    )
    (ROOT / 'sitemap.xml').write_text(xml, encoding='utf-8')
    print('  built: sitemap.xml')


def main():
    md = markdown.Markdown()
    articles_by_lang = {}

    for lang in ('ru', 'en'):
        for slug, cfg in TARGETS[lang].items():
            target = cfg['target']
            wrapper_class = cfg.get('class', 'md-content')
            suffix = '.en.md' if lang == 'en' else '.md'
            src = CONTENT / f'{slug}{suffix}'
            if not src.exists():
                print(f'  skip: content/{slug}{suffix} not found')
                continue
            if not target.exists():
                print(f'  skip: {target.relative_to(ROOT)} not found')
                continue

            md.reset()
            rendered = md.convert(src.read_text(encoding='utf-8'))
            block = f'<div class="{wrapper_class}">\n{rendered}\n</div>'
            inject(target, slug, block)

        articles = load_articles(lang)
        articles_by_lang[lang] = articles
        template = article_template(lang)
        for article in articles:
            render_article_page(md, article, lang, template)

        notes = load_notes(lang)
        notes_out = LANG_DIRS[lang] / 'data' / 'notes.json'
        generate_notes_json(md, notes, notes_out)

        articles_html = LANG_DIRS[lang] / 'articles.html'
        empty_text = '<p class="empty">скоро будет...</p>' if lang == 'ru' else '<p class="empty">coming soon...</p>'
        if articles_html.exists():
            block = ''.join(render_card(a, lang) for a in articles) if articles else empty_text
            inject(articles_html, 'articles-list', block)

        index_html = LANG_DIRS[lang] / 'index.html'
        if index_html.exists():
            preview = articles[:3]
            block = ''.join(render_card(a, lang) for a in preview) if preview else empty_text
            inject(index_html, 'articles-home', block)

    generate_sitemap(articles_by_lang)

    print('done.')

if __name__ == '__main__':
    main()

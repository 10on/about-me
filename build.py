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
import hashlib
import html
import json
import re
import sys
from pathlib import Path

try:
    import markdown
    from PIL import Image
except ImportError:
    print("Run: pip3 install markdown pillow", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent
CONTENT = ROOT / 'content'
ARTICLES_SRC = CONTENT / 'articles'
NOTES_SRC = CONTENT / 'notes'

SITE_URL = 'https://10on.github.io/about-me'
STATIC_PAGES = [
    '', 'notes.html', 'articles.html', 'about.html',
    'lego.html', 'retro.html', 'diy.html', 'games.html', 'projects.html', 'wishlist.html',
]

NAV_LABELS = {
    'ru': {'notes': 'заметки', 'articles': 'статьи', 'lego': 'лего', 'retro': 'ретро',
           'diy': 'самоделки', 'games': 'игры', 'wishlist': 'хотелки', 'about': 'обо мне'},
    'en': {'notes': 'notes', 'articles': 'articles', 'lego': 'lego', 'retro': 'retro',
           'diy': 'DIY', 'games': 'games', 'wishlist': 'wishlist', 'about': 'about'},
}
BRAND = {'ru': 'дэнчик', 'en': 'Denchik'}
TAGLINE = {'ru': 'лего · ретро · самоделки · разработка', 'en': 'lego · retro · DIY · dev'}
STRINGS = {
    'ru': {'theme_title': 'тема', 'email': 'почта', 'all_articles': '← все статьи', 'read_more': 'читать →',
           'open_note': 'Открыть заметку →'},
    'en': {'theme_title': 'theme', 'email': 'email', 'all_articles': '← all articles', 'read_more': 'read →',
           'open_note': 'Open note →'},
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
    template = """<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/svg+xml" href=\"""" + site_root + """favicon.svg">
    <link rel="icon" href=\"""" + site_root + """favicon.ico" sizes="any">
    <link rel="apple-touch-icon" href=\"""" + site_root + """apple-touch-icon.png">
    <title>{{title}} — """ + BRAND[lang] + """</title>
    <meta name="description" content="{{description}}">
    <link rel="canonical" href="{{url}}">
    <meta property="og:type" content="article">
    <meta property="og:locale" content=\"""" + ('ru_RU' if lang == 'ru' else 'en_US') + """\">
    <meta property="og:locale:alternate" content=\"""" + ('en_US' if lang == 'ru' else 'ru_RU') + """\">
    <meta property="og:site_name" content=\"""" + BRAND[lang] + """\">
    <meta property="og:title" content="{{title}} — """ + BRAND[lang] + """">
    <meta property="og:description" content="{{description}}">
    <meta property="og:url" content="{{url}}">
    <meta property="og:image" content="https://10on.github.io/about-me/img/persik.jpg">
    <meta property="og:image:width" content="1000">
    <meta property="og:image:height" content="882">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:image" content="https://10on.github.io/about-me/img/persik.jpg">
    <script type="application/ld+json">
{{json_ld}}
    </script>
    <script>try{{var t=localStorage.getItem('denchik-theme');if(t)document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}</script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=Space+Mono:wght@400;700&display=swap">
    <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet" media="print" onload="this.media='all'">
    <noscript><link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet"></noscript>
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
    </header>
    <nav>
        <a href="../notes.html">""" + nav['notes'] + """</a>
        <a href="../articles.html" class="active">""" + nav['articles'] + """</a>
        <a href="../lego.html">""" + nav['lego'] + """</a>
        <a href="../retro.html">""" + nav['retro'] + """</a>
        <a href="../diy.html">""" + nav['diy'] + """</a>
        <a href="../games.html">""" + nav['games'] + """</a>
        <a href="../wishlist.html">""" + nav['wishlist'] + """</a>
        <a href="../about.html">""" + nav['about'] + """</a>
    </nav>

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
"""
    return template.format(lang=lang)


def note_share_template(lang):
    """Lightweight standalone page for a single note: exists only so a shared link to
    notes/<id>.html carries per-note OG/Twitter tags (title/description/image) for link
    unfurlers like Telegram, which don't run JS and can't see a #fragment. It immediately
    redirects a real visitor into notes.html#note-<id> (scrolled to the note in context)."""
    site_root = '../' if lang == 'ru' else '../../'
    brand = BRAND[lang]
    open_note = STRINGS[lang]['open_note']
    template = """<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/svg+xml" href=\"""" + site_root + """favicon.svg">
    <link rel="icon" href=\"""" + site_root + """favicon.ico" sizes="any">
    <title>{{title}} — """ + brand + """</title>
    <meta name="description" content="{{description}}">
    <meta name="robots" content="noindex">
    <link rel="canonical" href="{{canonical}}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content=\"""" + brand + """\">
    <meta property="og:title" content="{{title}} — """ + brand + """">
    <meta property="og:description" content="{{description}}">
    <meta property="og:url" content="{{canonical}}">
    <meta property="og:image" content="{{image}}">
    <meta property="og:image:width" content="{{image_width}}">
    <meta property="og:image:height" content="{{image_height}}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:image" content="{{image}}">
    <meta http-equiv="refresh" content="0; url={{redirect}}">
    <link rel="stylesheet" href=\"""" + site_root + """style.css">
</head>
<body>
    <div class="container" style="padding-top: 2.5rem;">
        <p class="note-text">{{description}}</p>
        <p><a href="{{redirect}}">""" + open_note + """</a></p>
    </div>
    <script>location.replace({{redirect_js}});</script>
</body>
</html>
"""
    return template.format(lang=lang)


def strip_note_html(rendered):
    """Flatten a rendered note's HTML (paragraphs joined by <br><br>, may contain <img>)
    down to plain text, for use in a meta description / og:title."""
    text = re.sub(r'<br\s*/?>', ' ', rendered)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def truncate_text(text, length):
    if len(text) <= length:
        return text
    cut = text[:length].rsplit(' ', 1)[0]
    return cut.rstrip(',.;:—-') + '…'


def first_image_src(rendered):
    m = re.search(r'<img[^>]+src="([^"]+)"', rendered)
    return m.group(1) if m else None


def image_dimensions(rel_path):
    try:
        with Image.open(ROOT / rel_path) as im:
            return im.size
    except (OSError, FileNotFoundError):
        return None


def render_note_share_page(note, lang, template):
    lang_root = SITE_URL if lang == 'ru' else f'{SITE_URL}/en'
    canonical = f"{lang_root}/notes/{note['id']}.html"
    redirect = f"../notes.html#note-{note['id']}"
    text = strip_note_html(note['rendered'])
    title = truncate_text(text, 70)
    description = truncate_text(text, 160)

    img_src = first_image_src(note['rendered'])
    if img_src:
        image = f'{SITE_URL}/{img_src}'
        dims = image_dimensions(img_src) or (1000, 882)
    else:
        image = f'{SITE_URL}/img/persik.jpg'
        dims = (1000, 882)

    page_html = template.format(
        title=html.escape(title, quote=True),
        description=html.escape(description, quote=True),
        canonical=canonical,
        image=image,
        image_width=dims[0],
        image_height=dims[1],
        redirect=redirect,
        redirect_js=json.dumps(redirect),
    )
    out_dir = LANG_DIRS[lang] / 'notes'
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{note['id']}.html"
    out_path.write_text(page_html, encoding='utf-8')
    print(f"  built: {'en/' if lang == 'en' else ''}notes/{note['id']}.html")


def to_iso_date(date_str):
    """Convert a 'DD.MM.YYYY' front-matter date to ISO 8601 'YYYY-MM-DD' (schema.org/sitemap need ISO)."""
    m = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', date_str)
    if not m:
        return date_str
    day, month, year = m.groups()
    return f'{year}-{month}-{day}'


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


def article_json_ld(article, lang, url):
    data = {
        '@context': 'https://schema.org',
        '@type': 'BlogPosting',
        'headline': article['title'],
        'description': article['excerpt'],
        'datePublished': to_iso_date(article['date']),
        'inLanguage': lang,
        'url': url,
        'image': 'https://10on.github.io/about-me/img/persik.jpg',
        'author': {'@type': 'Person', 'name': 'Денис Пушкарёв', 'url': f'{SITE_URL}/about.html'},
        'mainEntityOfPage': {'@type': 'WebPage', '@id': url},
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def render_article_page(md, article, lang, template):
    md.reset()
    body_html = md.convert(article['body'])
    tag_text = ' '.join(f'#{t}' for t in article['tags'])
    lang_root = SITE_URL if lang == 'ru' else f'{SITE_URL}/en'
    url = f"{lang_root}/articles/{article['slug']}.html"
    page_html = template.format(
        title=article['title'], tag_text=tag_text, date=article['date'],
        read=article['read'], body=body_html,
        description=html.escape(article['excerpt'], quote=True),
        url=url,
        json_ld=article_json_ld(article, lang, url),
    )
    out_dir = LANG_DIRS[lang] / 'articles'
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{article['slug']}.html"
    out_path.write_text(page_html, encoding='utf-8')
    print(f"  built: {'en/' if lang == 'en' else ''}articles/{article['slug']}.html")


def load_notes(lang):
    """Read content/notes/*.md for `lang`, newest first (filenames YYYY-MM-DD-slug[.en].md).
    `id` (the slug) is stable across ru/en for the same note and is used to link/scroll/share it."""
    notes = []
    for path in lang_files(NOTES_SRC, lang):
        meta, body = parse_front_matter(path.read_text(encoding='utf-8'))
        tags = [t.strip() for t in meta.get('tags', '').split(',') if t.strip()]
        notes.append({
            'id': slug_from_path(path, lang),
            'date': meta.get('date', ''),
            'tags': tags,
            'body': body.strip(),
        })
    return notes


def add_img_dimensions(rendered):
    """Inject width/height (read from the actual file) and loading=lazy into <img> tags,
    so the browser can reserve layout space before the image loads (avoids CLS)."""
    def repl(m):
        tag = m.group(0)
        src_m = re.search(r'src="([^"]+)"', tag)
        if not src_m:
            return tag
        try:
            with Image.open(ROOT / src_m.group(1)) as im:
                w, h = im.size
        except (OSError, FileNotFoundError):
            return tag
        attrs = f' width="{w}" height="{h}" loading="lazy"'
        return re.sub(r'\s*/?>$', attrs + ' />', tag)
    return re.sub(r'<img\b[^>]*>', repl, rendered)


def render_note_text(md, body):
    """Markdown body → flat HTML string (paragraphs joined with <br><br> instead of <p>),
    since notes.json feeds a single innerHTML string per note, not a full block layout."""
    md.reset()
    rendered = md.convert(body).strip()
    rendered = re.sub(r'^<p>', '', rendered)
    rendered = re.sub(r'</p>$', '', rendered)
    rendered = rendered.replace('</p>\n<p>', '<br><br>')
    return add_img_dimensions(rendered)


def generate_notes_json(notes, out_path, lang):
    """Expects each note to already carry a `rendered` field (see render_note_text)."""
    prefix = '../' if lang == 'en' else ''
    data = [
        {
            'id': n['id'],
            'date': n['date'],
            'tags': n['tags'],
            'text': n['rendered'].replace('src="img/', f'src="{prefix}img/'),
        }
        for n in notes
    ]
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'  built: {out_path.relative_to(ROOT)}')


NOTE_SHARE_ICON = ('<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3">'
                    '</circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle>'
                    '<line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>'
                    '<line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>')


def render_home_note_card(note, lang):
    """Same markup the client JS builds for a note-item, so the newest note can be baked
    into index.html at build time instead of only appearing after data/notes.json loads
    (avoids a render-blocking fetch on the LCP path and the layout shift from it)."""
    share_label = 'Поделиться' if lang == 'ru' else 'Share'
    expand_label = 'Показать полностью ↓' if lang == 'ru' else 'Show more ↓'
    prefix = '../' if lang == 'en' else ''
    text = note['rendered'].replace('src="img/', f'src="{prefix}img/')
    tags_html = ' '.join(f'#{t}' for t in note['tags'])
    return (
        f'<div class="note-item" id="note-{note["id"]}"><div class="note-meta"><span>{note["date"]}</span>'
        f'<span class="note-meta-right"><span class="note-tags">{tags_html}</span>'
        f'<button class="note-share" data-url="notes/{note["id"]}.html" title="{share_label}" '
        f'aria-label="{share_label}">{NOTE_SHARE_ICON}</button></span></div>'
        f'<p class="note-text">{text}</p>'
        f'<button class="note-expand-btn" type="button">{expand_label}</button></div>'
    )


def load_wishlist_tags(lang):
    """Read data/wishlist.json for `lang` (hand-maintained, not generated by this script)
    just to pull its tags into the shared tag vocabulary — see generate_tags_json."""
    path = LANG_DIRS[lang] / 'data' / 'wishlist.json'
    if not path.exists():
        return []
    try:
        items = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return []
    return [t for item in items for t in item.get('tags', [])]


def generate_tags_json(lang, notes, articles):
    """Union of tags across notes, articles, and the wishlist, so all three pick tag names
    from one shared vocabulary instead of drifting into near-duplicates (e.g. 'лего'/'lego')."""
    tags = set()
    for n in notes:
        tags.update(n['tags'])
    for a in articles:
        tags.update(a['tags'])
    tags.update(load_wishlist_tags(lang))
    out_path = LANG_DIRS[lang] / 'data' / 'tags.json'
    out_path.write_text(json.dumps(sorted(tags), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
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


def file_version(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


def apply_asset_versions():
    """Append ?v=<content-hash> to every style.css/main.js reference across all HTML pages
    (static and generated), so a Cloudflare edge cache with a long max-age (see _headers)
    is busted automatically whenever either file's content changes, instead of serving a
    stale copy for up to its full TTL."""
    style_version = file_version(ROOT / 'style.css')
    main_js_version = {'ru': file_version(ROOT / 'main.js'), 'en': file_version(ROOT / 'en' / 'main.js')}
    style_re = re.compile(r'href="((?:\.\./)*)style\.css(?:\?v=[a-f0-9]+)?"')
    main_re = re.compile(r'src="main\.js(?:\?v=[a-f0-9]+)?"')

    for html_path in ROOT.rglob('*.html'):
        lang = 'en' if html_path.is_relative_to(ROOT / 'en') else 'ru'
        text = html_path.read_text(encoding='utf-8')
        new_text = style_re.sub(lambda m: f'href="{m.group(1)}style.css?v={style_version}"', text)
        new_text = main_re.sub(f'src="main.js?v={main_js_version[lang]}"', new_text)
        if new_text != text:
            html_path.write_text(new_text, encoding='utf-8')
            print(f'  versioned: {html_path.relative_to(ROOT)}')


def generate_sitemap(articles_by_lang, notes_by_lang):
    urls = [f'{SITE_URL}/{page}' for page in STATIC_PAGES]
    urls += [f"{SITE_URL}/articles/{a['slug']}.html" for a in articles_by_lang['ru']]
    urls += [f'{SITE_URL}/en/{page}' for page in STATIC_PAGES]
    urls += [f"{SITE_URL}/en/articles/{a['slug']}.html" for a in articles_by_lang['en']]

    # lastmod: known precisely for articles (front-matter date) and for the list/home pages
    # that surface them (notes.html/articles.html/index.html use the newest item's date).
    # Other static pages have no reliable date source, so they're left without a lastmod.
    lastmod = {}
    for lang in ('ru', 'en'):
        lang_root = SITE_URL if lang == 'ru' else f'{SITE_URL}/en'
        articles = articles_by_lang.get(lang, [])
        notes = notes_by_lang.get(lang, [])
        latest_article = to_iso_date(articles[0]['date']) if articles else None
        latest_note = to_iso_date(notes[0]['date']) if notes else None
        for a in articles:
            lastmod[f"{lang_root}/articles/{a['slug']}.html"] = to_iso_date(a['date'])
        if latest_article:
            lastmod[f'{lang_root}/articles.html'] = latest_article
        if latest_note:
            lastmod[f'{lang_root}/notes.html'] = latest_note
        home_dates = [d for d in (latest_article, latest_note) if d]
        if home_dates:
            lastmod[f'{lang_root}/'] = max(home_dates)

    def render_url(u):
        d = lastmod.get(u)
        return f'  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>' if d else f'  <url><loc>{u}</loc></url>'

    body = '\n'.join(render_url(u) for u in urls)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'{body}\n'
        '</urlset>\n'
    )
    (ROOT / 'sitemap.xml').write_text(xml, encoding='utf-8')
    print('  built: sitemap.xml')


def generate_llms_full_txt(articles, notes):
    """Full-text companion to llms.txt (llmstxt.org convention): inlines every article and
    note body plus the about/retro/diy bio pages, so an LLM can read the whole site's content
    in one fetch instead of crawling each page. Russian only, matching llms.txt's page list —
    the English mirror under /en/ isn't duplicated here."""
    parts = [
        '# дэнчик (Denchik) — full content\n',
        '> Full-text dump of https://10on.github.io/about-me/ for LLMs. '
        'For a short page index instead, see /llms.txt. '
        'English mirror (not duplicated here): https://10on.github.io/about-me/en/\n',
    ]

    for slug, title in (('about', 'About'), ('retro', 'Retro'), ('diy', 'DIY')):
        src = CONTENT / f'{slug}.md'
        if src.exists():
            parts.append(f'## {title}\n\n{src.read_text(encoding="utf-8").strip()}\n')

    parts.append('## Articles\n')
    for a in articles:
        tag_text = ' '.join(f'#{t}' for t in a['tags'])
        parts.append(
            f"### {a['title']} ({a['date']}, {a['read']})\n\n"
            f"{tag_text}\n\n{a['body'].strip()}\n"
        )

    parts.append('## Notes\n')
    for n in notes:
        tag_text = ' '.join(f'#{t}' for t in n['tags'])
        parts.append(f"### {n['date']}\n\n{tag_text}\n\n{n['body'].strip()}\n")

    (ROOT / 'llms-full.txt').write_text('\n'.join(parts) + '\n', encoding='utf-8')
    print('  built: llms-full.txt')


def main():
    md = markdown.Markdown()
    articles_by_lang = {}
    notes_by_lang = {}

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
        for n in notes:
            n['rendered'] = render_note_text(md, n['body'])
        notes_by_lang[lang] = notes
        notes_out = LANG_DIRS[lang] / 'data' / 'notes.json'
        generate_notes_json(notes, notes_out, lang)
        generate_tags_json(lang, notes, articles)

        note_template = note_share_template(lang)
        for n in notes:
            render_note_share_page(n, lang, note_template)

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

            notes_empty = '<p class="empty">скоро будет...</p>' if lang == 'ru' else '<p class="empty">coming soon...</p>'
            home_note_block = render_home_note_card(notes[0], lang) if notes else notes_empty
            inject(index_html, 'home-notes', home_note_block)

    generate_sitemap(articles_by_lang, notes_by_lang)
    generate_llms_full_txt(articles_by_lang['ru'], notes_by_lang['ru'])
    apply_asset_versions()

    print('done.')

if __name__ == '__main__':
    main()

# whois Дэнчик

Личный сайт: заметки, статьи, LEGO, ретро-железо, самоделки и игры.

Сайт: https://10on.github.io/about-me

Статический сайт без фреймворков, на чистых HTML, CSS и JS. Есть две версии: русская в корне репозитория и английская в `en/`.

## Структура

- `*.html` — страницы сайта
- `content/` — исходники в markdown: заметки (`content/notes/`), статьи (`content/articles/`) и тексты страниц about, retro и diy
- `data/*.json` — данные для LEGO, проектов и игр
- `img/`, `files/` — картинки и вложения
- `build.py` — генерирует из markdown HTML-страницы, `data/notes.json` и `sitemap.xml`
- `style.css`, `main.js` — стили и скрипты

## Локальный запуск

```bash
python3 -m http.server 8000
```

Сайт откроется на http://localhost:8000.

## Сборка

```bash
pip3 install markdown pillow
python3 build.py
```

Запускать после любого изменения в `content/`.

## Как добавить контент

- **Заметка**: создать файл `content/notes/YYYY-MM-DD-slug.md` с полями `date` и `tags` в начале файла. Если на эту дату уже есть заметка, добавить ещё поле `time`. Английская версия кладётся рядом в файл `.en.md`.
- **Статья**: создать файл `content/articles/YYYY-MM-DD-slug.md` с полями `title`, `tags`, `date`, `read` и `excerpt` в начале файла.
- **LEGO и игры**: отредактировать `data/*.json`, а для английской версии — `en/data/*.json`.

После этого запустить `python3 build.py`.

## Деплой

Сайт деплоится автоматически при пуше в `master`:

- **GitHub Pages** собирает сайт сам через GitHub Actions (`.github/workflows/pages.yml`).
- **Cloudflare Pages** раздаёт файлы из коммита как есть, без сборки. Поэтому перед пушем нужно запустить `build.py` и закоммитить сгенерированные файлы.

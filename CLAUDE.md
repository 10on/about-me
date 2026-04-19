# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Personal website for Дэнчик. Static site deployed on Cloudflare Pages. No build step — plain HTML/CSS/JS.

## Local development

Open `index.html` via a local HTTP server (required for `fetch()` to load JSON):

```bash
python3 -m http.server 8000
# or
npx serve .
```

## Architecture

- `index.html` — single page, all sections on one scroll
- `style.css` — all styles, CSS custom properties in `:root`
- `main.js` — fetches JSON files and renders each section
- `data/*.json` — content for each section (lego, retro, diy)

## Adding content

Edit the relevant JSON file in `data/`. Each item supports:

```json
{
  "name": "...",
  "desc": "...",         // optional
  "status": "want|have|done|wip",  // optional
  "url": "https://..."  // optional, makes name a link
}
```

## Deploying to Cloudflare Pages

Connect the repo in Cloudflare Pages dashboard:
- Build command: _(leave empty)_
- Output directory: `/` (root)

Every push to `main` deploys automatically.

## Design tokens

All colors and fonts are in `style.css` `:root`. Accent color is `--accent: #C85A2A`.

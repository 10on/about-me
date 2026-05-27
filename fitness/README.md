# 💪 Качалка — Fitness App

Веб-приложение для тренировок с Web Push уведомлениями. Работает на Cloudflare Workers + KV.

## Стек

| Слой | Технология |
|------|-----------|
| Frontend | Vanilla HTML/CSS/JS |
| Backend | Cloudflare Worker |
| БД | Cloudflare KV |
| Push | Web Push API + VAPID |
| Cron | Cloudflare Cron Triggers |
| Deploy | GitHub → Cloudflare (auto) |

## Структура

```
fitness/
├── index.html          # SPA
├── style.css
├── app.js              # Frontend логика
├── sw.js               # Service Worker (push)
├── worker/
│   └── index.js        # Cloudflare Worker (API + cron)
├── wrangler.toml       # Конфиг воркера
├── package.json
└── scripts/
    └── generate-vapid.js  # Генерация VAPID ключей (запустить 1 раз)
```

## Деплой

### 1. Создать KV Namespace в Cloudflare

В [Cloudflare Dashboard](https://dash.cloudflare.com) → Workers & Pages → KV:
- Создать namespace `fitness-kv`
- Скопировать ID в `wrangler.toml`:

```toml
[[kv_namespaces]]
binding = "FITNESS_KV"
id = "ВАШ_KV_ID"
preview_id = "ВАШ_PREVIEW_KV_ID"
```

### 2. Сгенерировать VAPID ключи

```bash
cd fitness
npm install
node scripts/generate-vapid.js
```

Скопируй вывод.

### 3. Установить секреты воркера

Через Cloudflare Dashboard → Workers → fitness-worker → Settings → Variables:

| Переменная | Тип | Значение |
|-----------|-----|---------|
| `VAPID_PRIVATE_KEY_JWK` | Secret | JSON из generate-vapid.js |
| `VAPID_PUBLIC_KEY` | Secret | base64url строка из generate-vapid.js |
| `VAPID_SUBJECT` | Secret | `mailto:твой@email.com` |

Или через CLI:
```bash
wrangler secret put VAPID_PRIVATE_KEY_JWK
wrangler secret put VAPID_PUBLIC_KEY
wrangler secret put VAPID_SUBJECT
```

### 4. Обновить URL воркера в index.html

```html
<script>window.WORKER_URL = "https://fitness-worker.ТВОЙ_АККАУНТ.workers.dev";</script>
```

### 5. Подключить GitHub → Cloudflare

#### Worker (API + Cron):
- Dashboard → Workers & Pages → Create → Import from GitHub
- Root directory: `fitness`
- Build command: _(пусто)_

#### Pages (Frontend):
- Dashboard → Workers & Pages → Pages → Connect GitHub
- Build command: _(пусто)_
- Output directory: `fitness`

### 6. Настроить CORS

В `wrangler.toml` обнови:
```toml
[vars]
FRONTEND_URL = "https://твой-сайт.pages.dev"
```

## Локальная разработка

```bash
cd fitness
npm install
npx wrangler dev worker/index.js --kv FITNESS_KV
```

Открой `index.html` через `python3 -m http.server 8000` или `npx serve .`

## Функционал

- ✅ Создание карточек упражнений (название, описание, подходы, повторения, длительность)
- ✅ Расписание: дни недели + время напоминания
- ✅ Отметить выполненным (счётчик + сегодня)
- ✅ Включить/отключить упражнение
- ✅ Web Push уведомления (Android Chrome, Firefox)
- ✅ Ежедневные напоминания через Cron Trigger
- ✅ Автошифрование payload (RFC 8291) без Node.js зависимостей
- ✅ Автоочистка умерших подписок

## Как работают пуши

```
[Cloudflare Cron 07:00 UTC]
       ↓
[Worker: читает KV → список упражнений]
       ↓
[VAPID JWT подписывается через Web Crypto]
       ↓
[Payload шифруется RFC 8291 (ECDH + AES-128-GCM)]
       ↓
[HTTP POST → push.services.mozilla.com / fcm.googleapis.com]
       ↓
[Service Worker на телефоне получает push]
       ↓
[showNotification() — тап открывает приложение]
```

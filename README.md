# tg-panel

Self-hosted admin panel for managing multiple Telegram bots — real-time inbox,
broadcast, quick-reply templates, multi-admin, i18n (EN / RU / UZ), dark mode.

**Stack:** FastAPI · SQLAlchemy 2 · PostgreSQL 16 · React 18 + Vite · Tailwind.

## Pages

- **Dashboard** — bot list, stats, add/edit/delete (superadmin).
- **Inbox** — two-panel chat with search, tags, polling, media, templates.
- **Broadcast** — send to one bot or all, live progress.
- **Templates** — reusable reply snippets.
- **Channels** — for any bot, browse the channels/groups it belongs to and
  fetch live info (members, admins, description). Each refresh is cached in
  the database, so the last snapshot loads instantly next time.
- **Users** — admin accounts (superadmin only).

Language and theme switchers are at the bottom of the sidebar.

---

## Project structure

```
backend/    FastAPI app, database models, Alembic migrations
frontend/   React + Vite single-page app
devops/     Docker and nginx files for production
```

### backend/

The API and all business logic. Run it with `make dev`; database schema
changes are managed by Alembic migrations (`make upgrade`). Configuration
comes from `backend/.env` (copy it from `backend/.env.example`).

### frontend/

The admin UI. A standalone Vite app that talks to the backend over
`/api/v1`. Run it with `npm run dev`; `npm run build` produces the static
files served in production.

### devops/

Everything needed to run the stack with Docker (PostgreSQL stays external):

- `docker-compose.yml` — backend, frontend, nginx.
- `nginx/default.conf` — reverse proxy; HTTP by default, with a commented
  HTTPS block to uncomment when you add TLS.
- `deploy.md` — step-by-step server deployment guide.

---

## Local development

### 1. Prerequisites

- Python 3.12+ and `uv` (`pip install uv`)
- Node.js 20+ and npm
- PostgreSQL 16 running on `localhost:5432`
- A bot token from [@BotFather](https://t.me/BotFather)

Create the database:

```bash
sudo -u postgres psql -c "CREATE DATABASE tgpanel;"
```

### 2. Backend

```bash
cd backend
cp .env.example .env       # set SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD
uv sync
make upgrade               # run migrations
make dev                   # http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                # http://localhost:5173
```

Sign in at **http://localhost:5173/manage/login** with the credentials from
`backend/.env`.

### 4. ngrok (for Telegram webhooks)

Telegram only delivers updates to public HTTPS URLs, so the backend on
`localhost:8000` must be exposed through a tunnel. Without this the UI works,
but incoming messages won't arrive.

Authenticate ngrok once with your token from the
[ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken):

```bash
ngrok config add-authtoken <YOUR_NGROK_AUTHTOKEN>
ngrok http 8000
```

Put the printed `https://...ngrok-free.app` URL in `backend/.env` and restart
the backend so the webhook is re-registered:

```bash
WEBHOOK_BASE_URL=https://<your-subdomain>.ngrok-free.app
```

On the free plan the URL changes on every ngrok restart — update
`WEBHOOK_BASE_URL` again whenever it does.

---

## Deployment

Running the stack on a server (Docker, external PostgreSQL, optional HTTPS)
is covered in **[`devops/deploy.md`](./devops/deploy.md)**.

---

## Key environment variables

| Variable             | Purpose                                          |
|----------------------|--------------------------------------------------|
| `SECRET_KEY`         | JWT signing secret (required when `DEBUG=False`)  |
| `DATABASE_URL`       | External PostgreSQL connection string            |
| `DEBUG`              | `True` for local HTTP; `False` for production HTTPS |
| `WEBHOOK_BASE_URL`   | Public HTTPS URL for Telegram webhooks (empty = off) |
| `FRONTEND_URL`       | Allowed CORS origin                              |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Auto-create superuser on first start |
| `ADMIN_LOGIN_PATH`   | Login URL (default `/manage/login`)              |

See `backend/.env.example` for the full list.

## License

[MIT](./LICENSE)

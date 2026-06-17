# Deploy guide

Docker deployment. PostgreSQL is **external** (not in the compose file).
Plain **HTTP** by default; HTTPS is opt-in. Run all commands from `devops/`.

## Requirements

- Docker Engine 24+ with Compose v2
- A reachable PostgreSQL 16 with an empty `tgpanel` database
- A bot token from [@BotFather](https://t.me/BotFather)
- *For HTTPS:* a domain pointing at the server, ports 80 / 443 open

## 1. Get the code

```bash
git clone <your-repo-url> tg-panel
cd tg-panel/devops
```

## 2. Configure `../backend/.env`

```bash
cp ../backend/.env.example ../backend/.env
```

```ini
SECRET_KEY=<long random string>
# host.docker.internal = Postgres on this server; or use a real/remote host
DATABASE_URL=postgresql://postgres:<PASSWORD>@host.docker.internal:5432/tgpanel
DEBUG=True                 # True for HTTP; False for HTTPS
WEBHOOK_BASE_URL=          # empty for HTTP; https URL for production
FRONTEND_URL=http://localhost
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<strong password>
```

For a host-local Postgres, let Docker connect: `listen_addresses = '*'` in
`postgresql.conf` and `host all all 172.16.0.0/12 scram-sha-256` in `pg_hba.conf`.

## 3. Run (HTTP)

```bash
docker compose up -d --build
```

Open `http://<server-ip>/manage/login` and sign in. Migrations run and the
superuser is created automatically on first boot.

> Telegram webhooks need HTTPS — bot messages won't arrive over HTTP, but the
> panel itself works fully.

## 4. Enable HTTPS (optional)

Port 443 and the cert mounts are already in `docker-compose.yml`; you only edit
`nginx/default.conf`.

```bash
sudo mkdir -p /var/www/certbot
sudo certbot certonly --webroot -w /var/www/certbot -d yourdomain.com
```

1. In `nginx/default.conf`: comment the **HTTP-ONLY** block, uncomment the two
   **HTTPS** blocks, set your domain.
2. In `../backend/.env`: `DEBUG=False`, `WEBHOOK_BASE_URL=https://yourdomain.com`,
   `FRONTEND_URL=https://yourdomain.com`.
3. Apply: `docker compose up -d --force-recreate`

Renew (cron): `sudo certbot renew --webroot -w /var/www/certbot && docker compose restart nginx`

## Update / common commands

```bash
git pull && docker compose up -d --build   # update to the latest code
docker compose logs -f backend             # follow backend logs
docker compose down                        # stop (external DB untouched)
pg_dump -h <db-host> -U postgres tgpanel > backup.sql   # backup
```

## Troubleshooting

- **Login does nothing (HTTP)** → set `DEBUG=True`; the `Secure` cookie is
  dropped over plain HTTP.
- **502 from nginx** → backend still booting or crashed: `docker compose logs backend`.
- **Backend can't reach the DB** → check `pg_hba.conf` / `listen_addresses`. Test:
  `docker compose exec backend python -c "import socket; socket.create_connection(('host.docker.internal',5432),3)"`
- **Bot gets no messages** → HTTPS + valid cert + `WEBHOOK_BASE_URL` required;
  check `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`.
- **Can't log in despite `ADMIN_*`** → auto-superuser is skipped if one exists;
  reset the password or recreate the `tgpanel` database.

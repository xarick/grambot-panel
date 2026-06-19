# Deploy guide

Docker deployment. PostgreSQL is **external** (not in the compose file).
Plain **HTTP** by default; HTTPS is opt-in. Run all commands from `devops/`.

## Requirements

- Docker Engine 24+ with Compose v2
- A reachable PostgreSQL 14+ with an empty `tgpanel` database — if it runs on
  this same server, see [Host-local PostgreSQL](#host-local-postgresql) below
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

### Host-local PostgreSQL

Skip this whole section if your DB is remote/managed. It applies only when
Postgres runs on the **same server** and you point `DATABASE_URL` at
`host.docker.internal` (as shown above).

First find the config files — the version in the path is whatever you have
installed (14, 15, 16…), so don't hard-code it:

```bash
sudo -u postgres psql -c "SHOW config_file;"   # -> postgresql.conf
sudo -u postgres psql -c "SHOW hba_file;"       # -> pg_hba.conf
```

Then do **all three** — the container can't reach the DB until every one is set:

1. **Listen on all interfaces** — in `postgresql.conf`:
   ```ini
   listen_addresses = '*'
   ```
2. **Allow the Docker subnet** — append one line to `pg_hba.conf`:
   ```
   host    all    all    172.16.0.0/12    md5
   ```
   > Use `/12`, **not** `/16`. Compose runs the backend on its own bridge
   > network (`172.18.x`), while `host.docker.internal` resolves to `172.17.0.1`.
   > `172.16.0.0/12` (= `172.16.0.0`–`172.31.255.255`) covers both; `172.17.0.0/16`
   > misses the container and you get `no pg_hba.conf entry`. `md5` accepts both
   > md5- and scram-stored passwords; `scram-sha-256` is stricter.
3. **Open the firewall** — if `ufw` is active, allow that subnet **by source**:
   ```bash
   sudo ufw allow from 172.16.0.0/12 to any port 5432 proto tcp
   ```
   > Allow by source, not `in on docker0`: the traffic arrives on Compose's
   > `br-*` bridge, so an interface-scoped `docker0` rule never matches and the
   > connection silently times out.

Apply, create the empty DB, and make the password match `DATABASE_URL`:

```bash
sudo systemctl restart postgresql
sudo -u postgres psql -c "CREATE DATABASE tgpanel;"
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '<PASSWORD>';"
```

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
- **Backend `unhealthy` / migrations don't run** → read the real error first:
  `docker logs devops-backend-1` (or `docker compose logs backend`). Quick TCP
  test from inside the container (keep it on one line):
  `docker compose exec backend python -c "import socket; socket.create_connection(('host.docker.internal',5432),3); print('ok')"`
  Common host-local DB cases (see [Host-local PostgreSQL](#host-local-postgresql)):
    - `connection ... timed out` → host firewall is dropping it → add the `ufw`
      rule (step 3).
    - `no pg_hba.conf entry for host "172.18.x.x"` → add/fix the `/12` line, then
      `sudo systemctl reload postgresql`. Confirm what's actually loaded:
      `sudo -u postgres psql -c "SELECT address, netmask, auth_method FROM pg_hba_file_rules WHERE address LIKE '172.%';"`
      — netmask must be `255.240.0.0` (a `255.255.0.0` means it's still `/16`).
    - `password authentication failed` →
      `sudo -u postgres psql -c "ALTER USER postgres PASSWORD '<PASSWORD>';"`
- **Bot gets no messages** → HTTPS + valid cert + `WEBHOOK_BASE_URL` required;
  check `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`.
- **Can't log in despite `ADMIN_*`** → auto-superuser is skipped if one exists;
  reset the password or recreate the `tgpanel` database.

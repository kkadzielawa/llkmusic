# LLKMusic

A Django-based web portal for blues & jazz guitar/piano learning, containing a blog section, courses registration, and modern, responsive design.

---

## Technical Stack

- **Backend**: Django 5.2 LTS (Python 3.12)
- **Frontend**: HTML5, Vanilla CSS3, Vanilla Javascript
- **Database**: PostgreSQL in Docker, SQLite3 for the non-Docker fallback

---

## Setup and Installation

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. For local Docker development, set `DATABASE_URL` in `.env` to the Compose database host:
   ```env
   DATABASE_URL=postgres://llkmusic:llkmusic@db:5432/llkmusic
   ```
3. Start the stack:
   ```bash
   docker compose up --build
   ```
4. Create an admin user:
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

## Development

- Run tests:
  ```bash
  docker compose exec web python manage.py test
  ```
- Run checks:
  ```bash
  docker compose exec web python manage.py check
  docker compose exec web python manage.py check --deploy
  ```

If you prefer non-Docker local development, install dependencies with `pip install -r requirements.txt` and run:

```bash
python manage.py migrate
python manage.py runserver
```

## Production

Use `docker-compose.prod.yml` on the DigitalOcean droplet with a populated `.env`:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

The production stack uses Gunicorn, PostgreSQL, and Caddy for HTTPS termination and media file serving.

Current production values:

- Droplet user: `kkadzielawa`
- App path: `/home/kkadzielawa/llkmusic`
- Production domain: `www.llkmusic.com`
- Apex redirect: `llkmusic.com` -> `https://www.llkmusic.com`
- Caddy / Let's Encrypt email: `kkadzi25@gmail.com`

For production, set at least these values in `.env` on the droplet:

```env
DEBUG=False
ALLOWED_HOSTS=www.llkmusic.com,llkmusic.com
CSRF_TRUSTED_ORIGINS=https://www.llkmusic.com,https://llkmusic.com
SITE_URL=https://www.llkmusic.com
DATABASE_URL=postgres://llkmusic:replace-db-password@db:5432/llkmusic
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
POSTGRES_DB=llkmusic
POSTGRES_USER=llkmusic
POSTGRES_PASSWORD=replace-db-password
```

Contact form email delivery also requires SMTP settings. For Gmail, create an app password and use that instead of the normal Gmail account password:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_TIMEOUT=10
EMAIL_HOST_USER=your-sender@gmail.com
EMAIL_HOST_PASSWORD=replace-with-app-password
DEFAULT_FROM_EMAIL=LLKMusic <your-sender@gmail.com>
CONTACT_FORM_RECIPIENTS=kkadzi25@gmail.com
```

## Public form protection

Contact and checkout submissions use server-side protection without requiring a CAPTCHA service:

- A honeypot and signed form token reject filled spam traps, submissions without a valid token, and submissions made less than two seconds after loading a form. Tokens last 24 hours.
- Both endpoints share limits of five attempts per IP address (IPv6 /64) per ten-minute window and three valid submissions per email address per hour. HTTP 429 responses include `Retry-After`.
- Single-use tokens and ten-minute duplicate detection prevent repeated emails and orders. Failed contact email delivery releases the duplicate claim so the visitor can retry.
- Counters and claims live in the database, so protection works across Gunicorn workers and threads. Only keyed hashes are stored in the guard table; expired records are removed in bounded batches during submissions.
- Limits and time windows are defined by the `PUBLIC_FORM_*` settings in `llkmusic/settings.py`.

Apply migrations when deploying these changes. The existing container entrypoint does this automatically. Without Docker, run `python manage.py migrate`.

The production Compose service enables `TRUST_PROXY_IP` because Caddy overwrites `X-Real-IP` and the Django service is not exposed publicly. Keep this disabled when Django is directly reachable, and do not replace the trusted header with a visitor-supplied `X-Forwarded-For` value. If another CDN is placed in front of Caddy, configure its trusted proxy addresses before relying on forwarded client IPs.

Use a unique, private `SECRET_KEY` in production; the app refuses the example/development key when `DEBUG=False`. The key protects signed form tokens as well as Django sessions.

Django is upgraded to the [supported 5.2 LTS series](https://www.djangoproject.com/download/#supported-versions), and the SQL parser dependency includes the [latest security fixes](https://sqlparse.readthedocs.io/en/latest/changes.html). Static storage uses Django's current `STORAGES` configuration. Structured data is escaped before insertion into inline JSON-LD scripts.

### Email and further improvements

The site sends notifications only to `CONTACT_FORM_RECIPIENTS`, using your configured sender and the visitor's address as `Reply-To`. It does not send automated replies to arbitrary visitor addresses. These controls reduce abuse of website-generated mail; they do not filter unsolicited mail sent directly to your inbox.

For mail using an address at your own domain, verify SPF and DKIM with your email provider and configure DMARC through the domain's DNS provider. Those account/DNS settings are outside this repository and have not been verified or changed here. Google documents the setup in its [email sender guidelines](https://support.google.com/a/answer/81126).

If distributed spam continues, the next step is a server-verified challenge such as Turnstile plus edge request limits. Review real submissions before tightening limits, especially when visitors share an IP address. Good follow-up website work is to confirm course delivery and scheduling details, add previews with the owner's permission, and measure performance on real mobile devices.

## CI/CD

This repo now includes a GitHub Actions workflow at `.github/workflows/deploy.yml` that runs whenever the `deploy` branch receives a push.

- `main` is the local/staging branch.
- `deploy` is the production branch.
- Merge `main` into `deploy` to trigger a production deploy.

Release flow:

```bash
git checkout main
git pull origin main

git checkout deploy
git pull origin deploy
git merge main
git push origin deploy
```

The workflow does two things:

- Runs Django CI checks against PostgreSQL.
- SSHes into the DigitalOcean droplet and runs `scripts/deploy-production.sh`.
- Performs an HTTPS smoke check against `https://www.llkmusic.com/` after deploy.

Required GitHub repository secrets:

```text
DO_HOST
DO_USER
DO_SSH_KEY
DO_SSH_PORT
DO_APP_DIR
```

Expected droplet setup:

- Repo cloned at the same path as `DO_APP_DIR`
- Recommended values: `DO_USER=kkadzielawa` and `DO_APP_DIR=/home/kkadzielawa/llkmusic`
- Production `.env` present on the droplet
- Docker and Docker Compose available
- `docker compose` plugin installed on the droplet
- `scripts/deploy-production.sh` executable

The deploy script intentionally refuses to continue if the droplet checkout has uncommitted changes. That keeps production deploys predictable and prevents server-side edits from being silently overwritten. After that clean-worktree check passes, it hard-resets the production checkout to `origin/deploy`, which lets production recover cleanly from forced branch realignments.

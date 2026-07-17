# LLKMusic

A Django-based web portal for blues & jazz guitar/piano learning, containing a blog section, courses registration, and modern, responsive design.

---

## Technical Stack

- **Backend**: Django 4.2 LTS (Python 3.12)
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

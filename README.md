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

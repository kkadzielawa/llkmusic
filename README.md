# LLKMusic

A Django-based web portal for blues & jazz guitar/piano learning, containing a blog section, courses registration, and modern, responsive design.

---

## Technical Stack

- **Backend**: Django 4.2 LTS (Python 3.12)
- **Frontend**: HTML5, Vanilla CSS3 (Custom styling with Inter Google Font integration), Vanilla Javascript
- **Database**: SQLite3 (default, gitignored)

---

## Setup and Installation

1. **Clone the repository** (if not already done).
2. **Set up your environment variables**:
   Create a `.env` file in the root directory by copying the example template:
   ```bash
   cp .env.example .env
   ```
   Modify the values inside `.env` to suit your development/production environment.

3. **Install Dependencies**:
   Ensure you have Python 3.12+ installed, and install requirements:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations**:
   Run Django migrations to create the SQLite database tables:
   ```bash
   python manage.py migrate
   ```

5. **Create a Superuser**:
   To access the Django admin portal (`/admin/`):
   ```bash
   python manage.py createsuperuser
   ```

---

## Development

- **Run Server**:
  ```bash
  python manage.py runserver
  ```
  Open `http://127.0.0.1:8000/` in your browser.

- **Run Tests**:
  To execute the unit tests for the pages and blog apps:
  ```bash
  python manage.py test
  ```

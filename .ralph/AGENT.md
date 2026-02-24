# Agent Build Instructions

## Project Setup
```bash
# Install Python dependencies (Django 4.2)
pip install -r src/requirements.txt

# Apply database migrations
cd src && python manage.py migrate

# Create Django superuser (optional, for /admin/ panel)
python manage.py createsuperuser
```

## Running the Development Server
```bash
cd src && python manage.py runserver
# Visit http://localhost:8000 to create a tournament
```

## Running Tests
```bash
# Pure-Python scheduling algorithm tests (no Django needed)
python3 src/tests/test_scheduling.py

# Full Django test suite (requires Django installed + migrations applied)
cd src && python manage.py test tournament
```

## Project Structure
```
src/
  manage.py
  requirements.txt
  config/
    settings.py        # Django settings
    urls.py            # Root URL config
    wsgi.py
  tournament/
    models.py          # All data models
    views.py           # All views
    urls.py            # App URL patterns
    forms.py           # Form classes
    constants.py       # Cup list, status constants
    scheduling.py      # Group stage scheduler + bracket logic
    admin.py           # Django admin registration
    migrations/
      0001_initial.py  # Initial schema migration
    templates/
      tournament/
        base.html           # Base layout + CSS
        create.html         # Tournament creation form
        created.html        # Post-creation URL display
        dashboard.html      # Group stage + standings view
        vote.html           # Cup voting form
        group_results.html  # Group game results entry
        bracket.html        # Bracket tree view
        bracket_results.html # Bracket game results entry
  tests/
    test_scheduling.py  # Scheduling algorithm tests
```

## Key URLs
- `/` — Create tournament
- `/tournament/<viewer_token>/` — Read-only viewer
- `/tournament/<admin_token>/admin/` — Organizer group stage
- `/tournament/<admin_token>/bracket/` — Organizer bracket
- `/tournament/<admin_token>/game/<id>/vote/` — Cup voting
- `/tournament/<admin_token>/game/<id>/results/` — Group results
- `/tournament/<admin_token>/bracket/<id>/results/` — Bracket results
- `/tournament/<admin_token>/admin/bracket/generate/` — Generate bracket (POST)

## Key Learnings
- Scheduling algorithm: `compute_game_sizes` finds optimal 3/4 player groups given total slots
- Bracket seeding: snake pattern (0, N-1, 1, N-2, ...) fills groups of 4
- All templates use inline CSS for dark racing theme; no external dependencies
- Django admin token and viewer token use `secrets.token_urlsafe(24)` — safe against brute-force
- The migration (0001_initial.py) was written manually — if models change, regenerate with `manage.py makemigrations`
- `select_cup` in scheduling.py: each cup gets (votes+1) tickets; even unvoted cups can win

## Environment Variables
- `DJANGO_SECRET_KEY` — Production secret key (change from default!)
- `DJANGO_DEBUG` — Set to "False" in production
- `DJANGO_ALLOWED_HOSTS` — Comma-separated allowed hostnames

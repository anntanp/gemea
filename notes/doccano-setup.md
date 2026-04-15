# Doccano Setup Notes

## 1. Why `admin/` is inaccessible from source

The README's pip setup works against a released PyPI package, which ships pre-built assets. Running from the cloned source repo (`~/Documents/claude/doccano/`) breaks in three compounding ways.

### 1.1 Missing `backend/client/`

The frontend is not built. Django's settings reference:

```python
STATICFILES_DIRS = ["backend/client/dist/static/"]
```

That directory does not exist in the repo (requires `yarn build`).

### 1.2 `collectstatic` fails entirely

Django's `FileSystemFinder` raises `FileNotFoundError` for any missing `STATICFILES_DIRS` entry. The error aborts the whole `collectstatic` run, so `STATIC_ROOT` (`backend/staticfiles/`) stays empty — no admin CSS, no app JS.

### 1.3 The `doccano` CLI forces `DEBUG=False`

`backend/cli.py` hardcodes:

```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
```

`config/settings/production.py` sets `DEBUG = False`. With `DEBUG=False` and an empty `STATIC_ROOT`, WhiteNoise has nothing to serve for `/static/*`. Django admin loads as unstyled HTML — effectively unusable.

**Why the pip package doesn't have this problem:** the PyPI publish CI (`pypi-publish.yml`) runs `yarn build` and `collectstatic` before packaging. The wheel bundles `backend/client/dist/` and `backend/staticfiles/` so they are present at runtime. Running from source skips all that.

---

## 2. Setup script (`doccano/setup.sh`)

Fixes the three problems above and sets up a working development environment.

### 2.1 What it does

| Step | Purpose |
|---|---|
| Create stub `backend/client/dist/static/` | Satisfies `STATICFILES_DIRS` so `collectstatic` doesn't abort |
| Build frontend with `yarn` (if available) | Full Nuxt UI; otherwise stub HTML at `/` |
| Export `DJANGO_SETTINGS_MODULE=config.settings.development` | `DEBUG=True`; WhiteNoise dev finder serves admin CSS/JS from `django.contrib.admin` without a populated `STATIC_ROOT` |
| `python manage.py collectstatic` | Populates `backend/staticfiles/` |
| `migrate` + `create_roles` + `create_admin` | Full DB init and superuser creation |
| Write `doccano/run.sh` | Convenience script: starts web server + Celery together |

### 2.2 Usage

```bash
# Full setup (builds frontend if yarn is available)
bash setup.sh

# Skip frontend build; /admin/ works, main UI shows stub page
bash setup.sh --admin-only

# After setup: start web server + Celery worker
bash run.sh
```

Environment variable overrides (all optional):

```bash
ADMIN_USER=admin ADMIN_PASS=adminpass ADMIN_EMAIL=admin@example.com PORT=8000 bash setup.sh
```

### 2.3 Manual run commands (after setup)

```bash
# Terminal 1 — web server
source .venv/bin/activate
cd backend
DJANGO_SETTINGS_MODULE=config.settings.development \
SECRET_KEY=local-dev-secret-change-me \
python manage.py runserver 8000

# Terminal 2 — task queue (needed for file import/export)
source .venv/bin/activate
cd backend
DJANGO_SETTINGS_MODULE=config.settings.development \
SECRET_KEY=local-dev-secret-change-me \
celery --app=config worker --loglevel=info --concurrency=2
```

---

## 3. Key file locations

| File | Role |
|---|---|
| `backend/cli.py` | Entry point for `doccano` CLI; forces production settings |
| `backend/config/settings/base.py` | `STATICFILES_DIRS`, `STATIC_ROOT`, `DEBUG` defaults |
| `backend/config/settings/production.py` | Overrides `DEBUG=False` |
| `backend/config/settings/development.py` | Inherits base with `DEBUG=True` |
| `backend/config/urls.py` | `path("admin/", admin.site.urls)` — admin IS registered |
| `backend/api/management/commands/create_admin.py` | Wraps `createsuperuser`; sets password post-creation |
| `.github/workflows/pypi-publish.yml` | Runs `yarn build` + `collectstatic` before packaging |
| `doccano/setup.sh` | Source-based setup script (written in this session) |
| `doccano/run.sh` | Written by `setup.sh`; starts server + Celery |

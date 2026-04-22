# django-authkit

`django-authkit` is a reusable Django package that provides an auth API layer
built on Django's own authentication system.

The package uses:

- A package-owned custom user model configured as `AUTH_USER_MODEL = "authkit.User"`.
- Django's built-in auth flows, password hashing, authentication backends, admin
  compatibility, permissions, groups, and sessions where appropriate.
- Django `Group` as the role primitive.
- Django `Permission` for permission management.
- Django REST Framework for APIs.
- drf-spectacular for OpenAPI and Swagger integration.
- SimpleJWT for token-based API authentication.

This repository also contains an `example_django_app` for local demonstration.
That example app is intentionally outside the installable package.

## Clone And Run The Example App

Prerequisites:

- Docker with Docker Compose.
- `make`.

Clone the repo, then run the full example bootstrap and server flow:

```bash
git clone https://github.com/django-authkit/django-authkit.git
cd django-authkit
make example-dev
```

That command will:

- create `.env` from `.env.example` if it does not exist
- build the example app image
- run migrations
- create a reusable local superuser if missing
- start the example Django app on port `8000`

Open:

- Home: http://127.0.0.1:8010/
- Authkit API info: http://127.0.0.1:8010/authkit/
- Swagger UI: http://127.0.0.1:8010/authkit/docs/swagger/
- Redoc: http://127.0.0.1:8010/authkit/docs/redoc/
- Django admin: http://127.0.0.1:8010/admin/

Default local admin credentials come from `.env.example`:

```text
email: admin@example.com
password: admin12345
```

For a step-by-step flow instead:

```bash
cp .env.example .env
make example-build
make example-migrate
make example-superuser
make example-up
```

Useful example commands:

```bash
make example-bootstrap
make example-logs
make example-shell
make example-down
```

## Installation

Install from PyPI after a release is published:

```bash
python -m pip install django-authkit
```

Install from a local checkout:

```bash
python -m pip install /path/to/django-authkit
```

Install in editable mode while developing:

```bash
python -m pip install -e /path/to/django-authkit
```

Install from a git repository:

```bash
python -m pip install "django-authkit @ git+https://github.com/django-authkit/django-authkit.git"
```

For a private or personal repository, replace the URL with your actual git
remote:

```bash
python -m pip install "django-authkit @ git+https://github.com/<owner>/django-authkit.git"
```

For repeatable application installs, pin a tag or commit:

```bash
python -m pip install "django-authkit @ git+https://github.com/<owner>/django-authkit.git@v0.1.0"
```

Install optional dependency groups when needed:

```bash
python -m pip install "django-authkit[social] @ git+https://github.com/django-authkit/django-authkit.git"
python -m pip install -e "/path/to/django-authkit[dev,docs]"
```

The installable package only includes `authkit` from `src/authkit`. The
`tests`, `docs`, and `example_django_app` directories are repository assets and
are excluded from package distribution.

## Development Commands

Install the package with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Common commands:

```bash
make lint
make format
make test
make coverage
make build
```

Check built package artifacts before publishing:

```bash
python -m twine check dist/*
```

Example app commands:

```bash
make example-dev
make example-migrate
make example-superuser
make example-down
```

## Minimal Integration

For a fresh Django project, install the package, configure the custom user model
before the first migration, include the package URLs, then run migrations:

```bash
python -m pip install "django-authkit @ git+https://github.com/django-authkit/django-authkit.git"
```

```python
# settings.py
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "authkit",
]

AUTH_USER_MODEL = "authkit.User"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}
```

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("", include("authkit.urls")),
]
```

```bash
python manage.py migrate
```

## Consumer Django Setup

### 1. Install From Git

Use a direct git install for open-source or private git distribution:

```bash
python -m pip install "django-authkit @ git+https://github.com/django-authkit/django-authkit.git"
```

For a specific branch, tag, or commit:

```bash
python -m pip install "django-authkit @ git+https://github.com/django-authkit/django-authkit.git@main"
```

### 2. Add Required Apps

Add Django's auth/admin dependencies, DRF, SimpleJWT blacklist support,
drf-spectacular, and `authkit` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",

    "authkit",
]
```

### 3. Set The Custom User Model

Configure the package-owned user model before running migrations:

```python
AUTH_USER_MODEL = "authkit.User"
```

`authkit.User` is implemented under `authkit.users.models.User` and exported
through the installed Django app label as `authkit.User`.

### 4. Configure DRF And drf-spectacular

If the consuming project does not already configure DRF schema generation, add:

```python
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "My Project API",
    "DESCRIPTION": "Project API schema.",
    "VERSION": "1.0.0",
}
```

`django-authkit` also exposes package-level OpenAPI metadata through the
`AUTHKIT` setting:

```python
AUTHKIT = {
    "API_PREFIX": "authkit/",
    "OPENAPI_TITLE": "My Project Auth API",
    "OPENAPI_DESCRIPTION": "Authentication APIs provided by django-authkit.",
    "OPENAPI_VERSION": "1.0.0",
}
```

### 5. Include Package URLs

Include the package URLs once in the consuming project's root URLconf. The
package applies its own configurable prefix.

```python
from django.urls import include, path

urlpatterns = [
    path("", include("authkit.urls")),
]
```

By default, this exposes:

- `/authkit/`
- `/authkit/auth/`
- `/authkit/users/`
- `/authkit/roles/`
- `/authkit/permissions/`
- `/authkit/password-reset/`
- `/authkit/verification/`
- `/authkit/social-auth/`
- `/authkit/audit-logs/`
- `/authkit/schema/`
- `/authkit/docs/swagger/`
- `/authkit/docs/redoc/`

To move the package API under another path, change `AUTHKIT["API_PREFIX"]`:

```python
AUTHKIT = {
    "API_PREFIX": "api/auth/",
}
```

With that setting, the package info endpoint becomes `/api/auth/`.

### 6. Run Migrations

Run migrations after `AUTH_USER_MODEL` and `INSTALLED_APPS` are configured:

```bash
python manage.py migrate
```

Create an admin user with Django's normal command:

```bash
python manage.py createsuperuser
```

## Main Auth API Surface

`django-authkit` is intended to become the main authentication API surface for
the consuming Django project. Consumer projects should integrate auth, users,
roles, permissions, verification, password reset, social auth, and audit-log
read APIs through the package URLs.

The package still uses Django's built-in auth internals rather than replacing
them. Roles are Django `Group` records, permissions are Django `Permission`
records, passwords use Django password hashers, and admin/session compatibility
stays aligned with Django.

## Migration Caveat

Set this before the consuming project's first migration:

```python
AUTH_USER_MODEL = "authkit.User"
```

Changing `AUTH_USER_MODEL` after a Django project already has migrations and
tables is difficult and project-specific. `django-authkit` does not try to hide
or automate that migration because Django treats the user model as a foundational
schema decision.

## Google Social Auth

Install the social optional dependencies when using Google login:

```bash
python -m pip install "django-authkit[social] @ git+https://github.com/django-authkit/django-authkit.git"
```

Create an OAuth 2.0 Client ID in Google Cloud Console for the consuming project,
then configure:

```python
AUTHKIT = {
    "SOCIAL_AUTH_GOOGLE_CLIENT_ID": "your-google-oauth-client-id.apps.googleusercontent.com",
    "SOCIAL_AUTH_ALLOW_SIGNUP": True,
    "SOCIAL_AUTH_ALLOW_ACCOUNT_LINKING": True,
    "SOCIAL_AUTH_MARK_VERIFIED_EMAIL": True,
}
```

Clients should obtain a Google ID token using Google's OAuth/OpenID Connect
flow, then exchange it with:

```http
POST /authkit/social-auth/google/token/
```

Request body:

```json
{
  "id_token": "google-id-token"
}
```

Provider metadata is available at:

- `/authkit/social-auth/providers/`
- `/authkit/social-auth/providers/google/`

## Status

Reusable package foundation with auth, user, role, permission, password reset,
verification, social auth, audit log, and OpenAPI endpoints.

## Publishing

There are two supported installation paths:

1. Git install:

   ```bash
   python -m pip install "django-authkit @ git+https://github.com/<owner>/django-authkit.git@v0.1.0"
   ```

   This only requires pushing the repository and tagging a release. Consumers
   cannot install it with only `pip install django-authkit` from git alone.

2. Package index install:

   ```bash
   python -m pip install django-authkit
   ```

   This requires publishing the built package to PyPI or a private Python
   package index under the distribution name `django-authkit`.

Build and check the package:

```bash
make lint
make test
make build
python -m twine check dist/*
```

Publish to PyPI after creating a PyPI project/account and configuring trusted
publishing or an API token:

```bash
python -m twine upload dist/*
```

For TestPyPI:

```bash
python -m twine upload --repository testpypi dist/*
```

After publishing to PyPI, consumer projects can use:

```bash
python -m pip install django-authkit
```

This repository includes GitHub Actions workflows for open-source package
publishing:

- `.github/workflows/ci.yml` runs linting, tests, package build, and package
  metadata checks on pushes and pull requests.
- `.github/workflows/publish.yml` builds and publishes to PyPI when a release
  tag such as `v0.1.0` is pushed.

The publish workflow uses PyPI Trusted Publishing. Configure a PyPI trusted
publisher for:

- PyPI project name: `django-authkit`
- Owner: your GitHub user or organization
- Repository name: `django-authkit`
- Workflow name: `publish.yml`
- Environment name: `pypi`

Then publish a version with:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Once the workflow succeeds, anyone can install the latest release with:

```bash
python -m pip install django-authkit
```

Or pin a specific version:

```bash
python -m pip install django-authkit==0.1.0
```

## Release Checklist

1. Update `CHANGELOG.md`.
2. Confirm `src/authkit/__init__.py` and `pyproject.toml` have the same version.
3. Run `make lint`.
4. Run `make test`.
5. Run `make build`.
6. Inspect package contents and confirm `example_django_app`, `tests`, and
   `docs` are not included in the distribution.
7. Tag the release in git.
8. Publish artifacts with the repository's chosen package index workflow.

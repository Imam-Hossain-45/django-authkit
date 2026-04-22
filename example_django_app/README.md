# django-authkit example app

This is a minimal Django project that demonstrates integrating the local
`django-authkit` package.

The app is intentionally outside `src/` and is excluded from the installable
package distribution by packaging configuration.

## Local setup

```bash
cd example_django_app
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open:

- Home: http://127.0.0.1:8000/
- Authkit API info: http://127.0.0.1:8000/authkit/
- Swagger UI: http://127.0.0.1:8000/authkit/docs/swagger/
- Redoc: http://127.0.0.1:8000/authkit/docs/redoc/

## Docker setup

From the repository root:

```bash
make example-dev
```

This creates `.env` if needed, builds the image, runs migrations, creates the
demo superuser, and starts the app.

Default demo admin credentials:

```text
email: admin@example.com
password: admin12345
```

Important: this demo sets `AUTH_USER_MODEL = "authkit.User"` before migrations,
which is required for projects that use authkit as the main auth layer.

Useful root-level commands:

```bash
make example-bootstrap
make example-up
make example-logs
make example-down
```

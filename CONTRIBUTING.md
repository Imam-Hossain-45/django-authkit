# Contributing

Thanks for contributing to `django-authkit`.

## Development Setup

Use Python 3.12 or newer.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Common Commands

```bash
make lint
make format
make test
make coverage
make build
```

## Example App

The example app is for local demonstration only and is not distributed as part
of the package.

```bash
make example-dev
```

Open Swagger UI at:

```text
http://127.0.0.1:8000/authkit/docs/swagger/
```

## Contribution Guidelines

- Keep the package Django-only.
- Use Django's built-in auth primitives wherever practical.
- Use Django `Group` as the role model.
- Do not introduce a separate role model unless there is a clear need.
- Keep `AUTH_USER_MODEL = "authkit.User"` as the expected consumer setup.
- Prefer focused API/integration tests over excessive unit fragmentation.
- Keep changes small and compatible with existing public routes where possible.

## Before Opening A PR

Run:

```bash
make lint
make test
make build
```

If the change affects public behavior, update `README.md` and `CHANGELOG.md`.

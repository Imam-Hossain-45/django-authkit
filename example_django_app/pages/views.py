"""Views for the django-authkit example app."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse


def home(request: HttpRequest) -> HttpResponse:
    """Return a small integration guide for the local demo project."""
    html = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>django-authkit example</title>
        <style>
          body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont,
              "Segoe UI", sans-serif;
            line-height: 1.5;
            margin: 3rem auto;
            max-width: 760px;
            padding: 0 1rem;
          }
          code {
            background: #f4f4f5;
            border-radius: 4px;
            padding: 0.1rem 0.3rem;
          }
          li {
            margin: 0.4rem 0;
          }
        </style>
      </head>
      <body>
        <h1>django-authkit example</h1>
        <p>
          This minimal Django project installs the local package in editable
          mode and exposes authkit under <code>/authkit/</code>.
        </p>
        <ul>
          <li><a href="/authkit/">Authkit API info</a></li>
          <li><a href="/authkit/docs/swagger/">Swagger UI</a></li>
          <li><a href="/authkit/docs/redoc/">Redoc</a></li>
          <li><a href="/admin/">Django admin</a></li>
        </ul>
        <p>
          The project uses <code>AUTH_USER_MODEL = "authkit.User"</code>,
          Django REST Framework, drf-spectacular, SimpleJWT, and SQLite.
        </p>
      </body>
    </html>
    """
    return HttpResponse(html)

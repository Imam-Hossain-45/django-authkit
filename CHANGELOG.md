# Changelog

All notable changes to `django-authkit` will be documented in this file.

This project follows semantic versioning before stable releases where practical.

## 0.1.0 - Initial Development Release

### Added

- Reusable Django package using `src/authkit`.
- Package-owned custom user model: `authkit.User`.
- JWT authentication APIs using SimpleJWT.
- User management APIs.
- Password reset APIs using Django token mechanisms.
- Email verification APIs.
- Role APIs backed by Django `Group`.
- Permission APIs backed by Django `Permission`.
- Google social auth token exchange foundation.
- Append-only audit log model, admin integration, and read-only APIs.
- Unified package URL entrypoint with OpenAPI, Swagger UI, and Redoc.
- Reusable email delivery abstraction using Django's email backend.
- Dockerized example Django app outside the installable package.
- Pytest/pytest-django test suite and coverage configuration.

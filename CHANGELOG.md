# Changelog

All notable changes to `django-authkit` will be documented in this file.

This project follows semantic versioning before stable releases where practical.

## 0.1.2 - Flexible Admin API Authorization

### Changed

- Added configurable admin API access policy with support for default
  staff-plus-permission access, permission-only access, or superuser-only access.
- Applied the shared admin policy consistently across user, role, permission,
  and audit log management endpoints.
- Added test coverage for permission-only and superuser-only admin API modes.

## 0.1.1 - Documentation Refresh

### Changed

- Updated the README content shown on package indexes.

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

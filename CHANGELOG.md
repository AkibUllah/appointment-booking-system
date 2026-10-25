# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- API reference and curl-session screenshots in the README.
- CodeQL code scanning workflow (Python, JavaScript/TypeScript and Actions) and Dependabot updates for pip, npm, Docker and GitHub Actions.
- Roadmap tracked as GitHub issues under the v0.2.0 milestone.
- This changelog.

### Changed

- Demo seed data and test fixtures use fictional chamber names, addresses and phone numbers.
- CI workflow runs with a read-only `GITHUB_TOKEN` by default.

## [0.1.0] - 2026-10-25

First public release.

### Added

- Slot generation in Asia/Dhaka from weekly availability templates and date exceptions (leave, extra sittings), stored in UTC.
- Booking service with a unique slot key and optimistic locking to prevent double booking, plus cancellation and reschedule policies (cut-off hours, maximum reschedules, lead time, booking horizon).
- Bangladeshi phone normalisation for patient registration.
- Reminder job on APScheduler (24 h and 1 h before) through a console notifier that records every message.
- Public REST API (doctors, slots, patients, bookings) and token-protected admin API (doctors, availability, exceptions, bookings, stats, notifications).
- React + Vite frontend with doctor search, slot picker, booking flow, my appointments and an admin schedule editor, in English and Bangla.
- 51 backend tests and 25 frontend tests, CI for Python 3.10/3.11 and Node 18/20, docker compose with Postgres, a seed job and an nginx-served frontend.
- Live demo kit: Swagger UI on GitHub Pages, Codespaces dev container and Render blueprint.

### Fixed

- Managed Postgres URLs (`postgres://`) are accepted and the nginx upstream is configurable.

[Unreleased]: https://github.com/AkibUllah/appointment-booking-system/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/AkibUllah/appointment-booking-system/releases/tag/v0.1.0

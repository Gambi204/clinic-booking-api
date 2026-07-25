# AI Usage Log and Reflection

This document records how AI was used during the Savannah Informatics Backend Developer Take-Home Assessment, how suggestions were verified, and where AI guidance was corrected.

## Detailed Usage Log

| Date | Section | AI Used For | Suggestion or Output | Accepted, Modified, or Rejected | How It Was Verified |
|---|---|---|---|---|---|
| 2026-07-25 | Planning | Comparing FastAPI and Django for the assessment | Use FastAPI because it was the framework used most recently | Accepted | Checked against the assessment, which permits FastAPI, and verified by implementing all required endpoints |
| 2026-07-25 | Architecture | Selecting a reliable and zero-cost technical stack | FastAPI, PostgreSQL, SQLAlchemy, Alembic, pytest, GitHub Actions, and Render | Accepted with scope controls | Verified through implementation, PostgreSQL-backed tests, CI, and the public Render deployment |
| 2026-07-25 | Database foundation | Configuring PostgreSQL, SQLAlchemy, environment variables, and Alembic | Use a dedicated database role, Psycopg 3, a request-scoped session, and a secret `.env` file | Accepted after local verification | Verified through PostgreSQL, a direct SQLAlchemy query, Alembic connectivity, and the `/health` endpoint |
| 2026-07-25 | Data modelling | Designing the Doctor, Working Hours, Patient, and Appointment tables | Use typed SQLAlchemy models, fixed appointment duration, soft cancellation, and a PostgreSQL partial unique index | Accepted after migration and database inspection | Verified through Alembic autogeneration, direct PostgreSQL inspection, and migration downgrade/upgrade |
| 2026-07-25 | Seed data and test foundation | Designing repeatable seed data and isolated PostgreSQL test fixtures | Use an idempotent seed script, a separate test database, transaction rollback fixtures, and direct constraint tests | Accepted after execution | Verified by running the seed twice, checking record counts, running pytest, and inspecting test cleanup |
| 2026-07-25 | Continuous integration | Creating a GitHub Actions workflow for PostgreSQL-backed tests | Start a PostgreSQL 18 service, apply Alembic migrations, and run pytest on every pull request to `main` | Accepted after GitHub execution | Verified through real pull requests and successful GitHub Actions runs |
| 2026-07-25 | Scheduling domain | Designing timezone handling, slot generation, minimum notice, and reusable validation | Generate slots from working-period starts, normalize times to `Africa/Nairobi`, and use framework-independent validation errors | Accepted after edge-case testing | Verified through tests covering alignment, breaks, notice boundaries, past dates, timezone conversion, and booked slots |
| 2026-07-25 | Appointment creation API | Structuring request schemas, domain errors, API errors, database conflict handling, and deterministic endpoint tests | Use an injectable clock, framework-independent service errors, a global API error handler, and PostgreSQL constraint-name inspection | Accepted after API and database tests | Verified through successful, missing-resource, invalid-time, inactive-doctor, malformed-request, and duplicate-booking tests |
| 2026-07-25 | Doctor availability API | Designing date-range queries, available-slot responses, and cancellation-aware filtering | Query scheduled appointments within Nairobi date boundaries and reuse the tested slot engine | Accepted after API tests | Verified through working-day, non-working-day, scheduled, cancelled, inactive, missing-doctor, and past-date tests |
| 2026-07-25 | Appointment cancellation | Designing row locking, cancellation audit fields, repeated-cancellation handling, and slot-release tests | Use `SELECT FOR UPDATE`, preserve the record, require a reason, and verify that another patient can book the released slot | Accepted after API and database tests | Verified through successful cancellation, repeated cancellation, validation, missing-resource, and replacement-booking tests |
| 2026-07-25 | Appointment rescheduling | Designing atomic movement, row locking, conflict handling, and rollback verification | Lock the existing appointment, validate before mutation, update inside one transaction, and retain PostgreSQL uniqueness as the final concurrency safeguard | Accepted after API and database tests | Verified through successful movement, old-slot release, destination blocking, occupied-slot rollback, cancelled-state, validation, and malformed-request tests |
| 2026-07-25 | Patient appointments bonus endpoint | Designing the patient appointment query, response structure, relationship loading, and chronological filtering | Return only upcoming scheduled appointments, preload doctor details, and order by appointment time | Accepted after PostgreSQL-backed API tests | Verified through ordering, past-record exclusion, cancelled-record exclusion, empty results, missing-patient, and invalid-path tests |
| 2026-07-25 | Concurrent booking integration test | Adapting concurrency verification to the existing outer-transaction pytest fixture | Add a separate committed setup fixture, give each thread its own session, and synchronize both transactions immediately before commit | Accepted after repeated PostgreSQL-backed execution | Verified that exactly one booking succeeded, one returned `SLOT_UNAVAILABLE`, and only one scheduled database row existed |
| 2026-07-25 | API observability | Designing request correlation, structured logs, privacy-conscious fields, and validation-error consistency | Add request-ID middleware, JSON logs, response headers, and structured `422` responses without logging request bodies | Accepted after API and formatter tests | Verified generated and supplied request IDs, domain errors, validation errors, and JSON log fields |
| 2026-07-25 | Render deployment preparation | Designing a zero-cost Blueprint, PostgreSQL URL compatibility, migration execution, health checks, and CI-gated automatic deployment | Add `render.yaml`, normalize Render's PostgreSQL URL for Psycopg 3, run migrations and the idempotent seed at startup, and configure `/health` with `checksPass` automatic deployment | Accepted after local configuration and regression tests | Verified URL normalization, Alembic migration, repeatable seed execution, server startup, database health, and the complete test suite |
| 2026-07-25 | Live deployment | Planning production smoke tests and deployment evidence | Verify health, Swagger, request IDs, availability, booking, duplicate protection, rescheduling, cancellation, and automatic deployment after passing checks | Accepted after live execution | Verified against the public Render URL and recorded in `docs/DEPLOYMENT_VERIFICATION.md` |

## Corrections to AI Guidance

| Date | Area | Initial AI Guidance | Runtime Evidence and Correction | Final Verification |
|---|---|---|---|---|
| 2026-07-25 | FastAPI route inspection | The initial diagnostic assumed every `app.routes` entry had a `path` attribute and expected documentation routes in a filtered `APIRoute` result | FastAPI 0.140 returned an internal `_IncludedRouter`; route verification was changed to inspect `app.openapi()["paths"]` and perform an actual request | `/appointments` appeared in OpenAPI and Swagger, and an empty request returned `422` rather than `404` |
| 2026-07-25 | GitHub Actions Python setup | The initial workflow relied on implicit Python-version resolution | GitHub Actions warned that no Python version had been resolved, so Python `3.14.3` was pinned explicitly and the pip cache path was configured | The warning disappeared and the CI job passed |
| 2026-07-25 | FastAPI test-client dependency | The initial dependency suggestion used ordinary `httpx` | The installed Starlette version emitted a deprecation warning directing the project to `httpx2`; the dependency was changed after checking the runtime warning | The warning disappeared and all TestClient-based tests continued to pass |
| 2026-07-25 | CI infrastructure failure | A GitHub Actions run failed while pulling `postgres:18` | The error occurred before repository checkout or tests and was treated as a temporary Docker registry timeout rather than a code defect | Re-running the failed job succeeded without changing application code |

## Reflection

AI accelerated planning, scaffolding, edge-case identification, test design, troubleshooting, and documentation. It was particularly useful for proposing reusable service boundaries, PostgreSQL-backed integrity checks, deterministic clock injection, concurrency tests, and deployment verification steps.

AI output was not treated as authoritative. Every accepted code suggestion was read, adapted where necessary, run locally, and exercised through automated or live tests. The route-inspection, Python setup, and HTTP client examples above demonstrate that AI guidance was corrected when it conflicted with runtime evidence.

Final responsibility remained with the candidate. The candidate configured the local environment, executed migrations, inspected failures, ran the tests, reviewed pull requests, verified CI, deployed the service, and exercised the public endpoints.

## Candidate-Independent Decisions

The assessment requires two meaningful decisions made by Emmanuel without first requesting an AI recommendation. These must be recorded honestly in `docs/DECISIONS.md` and summarized here before submission.

Do not convert an AI-assisted decision into an independent decision retroactively. After making the two decisions personally, add:

1. The decision and the context in which it was made.
2. Why it was selected.
3. The trade-off accepted.
4. How it was verified.
5. A statement that AI was not consulted before the decision.

## Notes

- AI-generated code was not accepted without reading, running, testing, and understanding it.
- Incorrect or incomplete AI suggestions were recorded rather than hidden.
- No production database credentials or secrets were provided to AI or committed to the repository.
- Final architectural and implementation responsibility remains with the candidate.

# AI Usage Log

This document records how AI was used during the assessment.

| Date | Section | AI Used For | Suggestion or Output | Accepted, Modified, or Rejected | How It Was Verified |
|---|---|---|---|---|---|
| 2026-07-25 | Planning | Comparing FastAPI and Django for the assessment | Use FastAPI because it is the framework used most recently | Accepted | Checked against the assessment, which explicitly permits FastAPI |
| 2026-07-25 | Architecture | Selecting a reliable and free technical stack | FastAPI, PostgreSQL, SQLAlchemy, Alembic, pytest, GitHub Actions, and Render | Accepted with scope controls | Each technology will be verified through implementation, tests, and official documentation |
| 2026-07-25 | Database foundation | Configuring PostgreSQL, SQLAlchemy, environment variables, and Alembic | Use a dedicated database role, Psycopg 3, a request-scoped session, and a secret `.env` file | Accepted after local verification | Verified through `psql`, a direct SQLAlchemy query, Alembic connectivity, and the `/health` endpoint |
| 2026-07-25 | Data modelling | Designing the Doctor, Working Hours, Patient, and Appointment tables | Use typed SQLAlchemy models, fixed appointment duration, soft cancellation, and a PostgreSQL partial unique index | Accepted after migration and database inspection | Verified through Alembic autogeneration, direct PostgreSQL inspection, and migration downgrade/upgrade |
| 2026-07-25 | Seed data and test foundation | Designing repeatable seed data and isolated PostgreSQL test fixtures | Use an idempotent seed script, a separate test database, transaction rollback fixtures, and direct constraint tests | Accepted after execution | Verified by running the seed twice, checking record counts, running pytest, and inspecting test cleanup |

## Notes

- AI-generated code will not be accepted without reading, running, testing, and understanding it.
- Incorrect or incomplete AI suggestions will be recorded rather than hidden.
- Final architectural and implementation responsibility remains with the candidate.
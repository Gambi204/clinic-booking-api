# AI Usage Log and Reflection

This document answers the four AI-reflection questions in the Savannah Informatics Backend Developer Take-Home Assessment and records how I verified AI-assisted work.

## 1. What did I use AI for across the four sections?

### Section 1 - System design

I used AI to review model boundaries, relationships, scheduling assumptions, concurrency risks, and trade-offs. It helped me challenge the design rather than keeping all logic in route handlers.

I independently selected FastAPI before asking AI to review the implementation approach. AI was later used to help structure the FastAPI project and identify edge cases.

### Section 2 - API implementation

I used AI for:

- Suggestions on separating routes, schemas, services, models, and configuration.
- Reviewing timezone-aware slot generation and the one-hour notice rule.
- Proposing validation and structured error cases.
- Designing PostgreSQL-backed tests.
- Troubleshooting errors and warnings that appeared while I ran the project.
- Reviewing cancellation, rescheduling, and concurrent double-booking behavior.

I read and ran every accepted code suggestion. I did not treat generated code as correct until the tests and runtime behavior supported it.

### Section 3 - Deployment and CI/CD

I used AI to compare practical zero-cost deployment options, draft the GitHub Actions and Render Blueprint configuration, identify environment variables, and prepare a live smoke-test checklist.

AI presented CI/CD options, and I selected GitHub Actions because it integrated directly with my GitHub repository. Because AI influenced that choice, I have not counted it as one of my two decisions made without AI.

### Section 4 - Reflection and documentation

I used AI to help organize the README, decision log, deployment evidence, and this reflection. The factual content comes from the code I ran, the test results I observed, the pull requests I merged, and the live deployment I verified.

## 2. One example where an AI suggestion improved my work

The strongest improvement was the genuine concurrent-booking integration test.

My prompt was essentially:

> Help me design a PostgreSQL-backed test that forces two independent appointment-booking transactions to see the same doctor slot as free before either transaction commits, while preserving my existing rollback-based pytest fixtures.

The useful part of the suggestion was to:

- Keep the normal rollback fixture for most tests.
- Add a separate fixture for committed setup records.
- Give each worker thread its own SQLAlchemy session.
- Synchronize both workers immediately before commit.
- Verify both the service outcome and the final database row count.

This was better than simply sending the same request twice. A sequential duplicate request mainly proves the application-level conflict check. The synchronized test proves that PostgreSQL remains the final safeguard when two transactions race after both have seen the slot as available.

I verified the result by running the test repeatedly and confirming that:

- Exactly one booking succeeded.
- Exactly one booking returned `SLOT_UNAVAILABLE`.
- Exactly one scheduled appointment existed for the doctor and start time.

## 3. One example where AI output was wrong or incomplete

AI initially suggested inspecting the application routes with a list comprehension that assumed every item in `app.routes` had a `.path` attribute. It also expected documentation routes in a filtered list of FastAPI `APIRoute` objects.

My installed FastAPI version returned an internal `_IncludedRouter`, which caused:

```text
AttributeError: '_IncludedRouter' object has no attribute 'path'
```

I caught the problem because I ran the command instead of accepting it as correct.

I corrected the verification by:

- Inspecting `app.openapi()["paths"]`.
- Checking the route directly in the appointments router.
- Opening Swagger UI.
- Sending an empty request to `POST /appointments`.

The request returned `422`, not `404`, which proved the endpoint was registered and request validation was running.

Other AI guidance was also corrected when runtime evidence disagreed:

- I explicitly pinned Python `3.14.3` after GitHub Actions warned that no version had been resolved.
- I replaced ordinary `httpx` with `httpx2` after the installed Starlette version emitted a deprecation warning.
- I re-ran a CI job without changing code when Docker Hub timed out before checkout or test execution.

## 4. Two decisions I made without AI

### Decision 1 - Choose FastAPI instead of Django

I chose FastAPI before asking AI to review the implementation.

I trusted my judgment because I had used FastAPI in recent projects and understood its project structure, dependency injection, request validation, and automatic OpenAPI documentation. I believed I could build, debug, test, and explain the assessment more confidently with it within the available time.

The trade-off was accepting that FastAPI has less built-in structure and administration functionality than Django. I addressed that by creating a deliberate modular structure with separate routes, schemas, services, models, configuration, and middleware.

I verified the decision by implementing every required endpoint and both bonus requirements, running the PostgreSQL-backed test suite, and deploying the application successfully.

### Decision 2 - Build incrementally and merge only verified stages

At the start, I decided not to generate the whole solution in one pass. I worked one capability at a time in small feature or fix branches and moved forward only after the current stage worked locally.

I trusted my judgment because my previous development experience had shown me that small changes are easier to understand, debug, review, and reverse than one large unverified change.

The trade-off was creating more branches, commits, and pull requests, which took longer than committing everything at once.

I verified the approach through the repository history: database setup, scheduling, booking, availability, cancellation, rescheduling, patient appointments, concurrency, observability, and deployment were reviewed and merged separately after local tests and GitHub Actions passed.

## Detailed AI Usage Log

| Date | Area | What I used AI for | How I handled the output | Verification |
|---|---|---|---|---|
| 2026-07-25 | Framework review | Reviewing the implications of the FastAPI choice I had already made | Accepted implementation guidance, not the original framework decision | All required and bonus endpoints were implemented, tested, and deployed |
| 2026-07-25 | Architecture | Reviewing a zero-cost technical stack and modular project structure | Accepted with scope controls | Verified through implementation, CI, and the public deployment |
| 2026-07-25 | Database foundation | PostgreSQL, SQLAlchemy, environment variables, and Alembic setup | Accepted after local execution | Verified with SQLAlchemy connectivity, migrations, and `/health` |
| 2026-07-25 | Data modelling | Doctor, working-hours, patient, and appointment model review | Accepted after inspection and migration testing | Verified through Alembic upgrade/downgrade and direct constraint tests |
| 2026-07-25 | Seed and test foundation | Idempotent seed data and isolated PostgreSQL fixtures | Modified to match the local database setup | Verified by repeated seed runs and isolated tests |
| 2026-07-25 | CI | GitHub Actions workflow suggestions | I selected GitHub Actions after reviewing the suggestions | Verified through pull-request checks and `main` checks |
| 2026-07-25 | Scheduling | Timezones, slot generation, breaks, and minimum notice | Accepted after edge-case testing | Verified with deterministic scheduling tests |
| 2026-07-25 | Booking | Request schemas, service errors, conflict handling, and injectable time | Accepted after API and database tests | Verified across success, validation, missing-resource, and conflict cases |
| 2026-07-25 | Availability | Date boundaries and scheduled-slot filtering | Accepted after API tests | Verified for working days, non-working days, cancellations, and past dates |
| 2026-07-25 | Cancellation | Row locking, cancellation audit fields, and slot release | Accepted after API and database tests | Verified repeated cancellation and replacement booking behavior |
| 2026-07-25 | Rescheduling | Atomic movement, locking, conflict handling, and rollback | Accepted after API and database tests | Verified old-slot release, destination blocking, and failure rollback |
| 2026-07-25 | Patient bonus endpoint | Upcoming appointment query and ordering | Accepted after PostgreSQL-backed tests | Verified ordering and exclusion of past and cancelled records |
| 2026-07-25 | Concurrency | A real two-transaction booking race | Accepted after repeated execution | Verified one success, one conflict, and one final scheduled row |
| 2026-07-25 | Observability | Request IDs, JSON logs, and structured validation errors | Accepted after tests | Verified headers, error bodies, and formatter output |
| 2026-07-25 | Deployment | Render Blueprint, URL normalization, migrations, health checks, and smoke tests | Accepted after local and live verification | Verified against the public Render application |
| 2026-07-26 | Documentation | Reviewing requirement coverage, tense, clarity, and supporting evidence | Modified into my own final wording | Cross-checked against the assessment and implemented repository |

## Corrections and Rejected Assumptions

| Area | Initial issue | How I caught it | Correction |
|---|---|---|---|
| FastAPI route inspection | The command assumed every route entry had `.path` | Runtime `AttributeError` | Used OpenAPI inspection, Swagger, and a real request |
| GitHub Actions Python setup | Python version resolution was implicit | Workflow warning | Pinned Python `3.14.3` and configured the dependency cache |
| Test-client dependency | Ordinary `httpx` produced a Starlette deprecation warning | Local test output | Replaced it with `httpx2` and reran the suite |
| Docker service pull | PostgreSQL image pull timed out before the job reached the repository | CI logs showed failure during service startup | Re-ran the failed job without changing application code |

## Verification Principles I Followed

- I read and understood accepted AI-generated code before keeping it.
- I ran focused tests before running the full suite.
- I used PostgreSQL in tests instead of replacing database behavior with SQLite.
- I verified errors through their status code, machine-readable code, and final database state.
- I used runtime evidence to correct AI guidance.
- I did not commit `.env` or production database credentials.
- I remained responsible for the architecture, code, deployment, and submission.

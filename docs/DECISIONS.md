# Engineering Decision Log

| ID | Decision | Reason | Trade-off | AI Assisted |
|---|---|---|---|---|
| D-001 | Use FastAPI | Recent practical familiarity and automatic OpenAPI documentation | Less built-in administration than Django | Yes |
| D-002 | Use PostgreSQL | Strong transaction and constraint support | Requires database installation and configuration | Yes |
| D-003 | Use synchronous SQLAlchemy | Easier to understand, test, and explain for this assessment | Does not demonstrate asynchronous database access | Yes |
| D-004 | Use Render free tier | Meets the public deployment requirement at no cost | Service may sleep during inactivity | Yes |
| D-005 | Use Africa/Nairobi as clinic timezone | The clinic scenario and employer are based in Kenya | Multi-timezone clinics would need additional configuration | Yes |
| D-006 | Use Psycopg 3 as the PostgreSQL driver | It supports the selected Python and PostgreSQL versions and integrates with SQLAlchemy | The connection URL must explicitly identify the Psycopg driver | Yes |
| D-007 | Load secrets through environment variables | Prevents database credentials from being committed to source control | Local developers must create their own `.env` file | Yes |
| D-008 | Use one SQLAlchemy session per API request | Provides clear transaction boundaries and prevents sessions from being shared concurrently | Each request creates and closes its own session | Yes |
| D-009 | Store fixed appointment duration implicitly | Every appointment lasts 30 minutes, so only the start time must be stored | Variable durations would require a future duration or end-time column | Yes |
| D-010 | Keep cancelled appointments rather than deleting them | Preserves operational history and releases the slot through status | The appointments table retains more records over time | Yes |
| D-011 | Use a PostgreSQL partial unique index for scheduled doctor slots | Prevents concurrent double-booking while allowing cancelled historical appointments | This index is PostgreSQL-specific | Yes |
| D-012 | Represent working hours as multiple weekday periods | Supports lunch breaks and differing schedules without a separate break model | Overlapping periods are not currently prevented by a database exclusion constraint | Yes |
| D-013 | Use string status values with a database check constraint | Simpler migrations than a PostgreSQL-native enum while retaining database validation | Status values occupy slightly more storage than a native enum | Yes |
| D-014 | Use a separate PostgreSQL database for automated tests | Prevents tests from damaging local development data and exercises PostgreSQL-specific behaviour | Local setup requires creating one additional database | Yes |
| D-015 | Roll back an outer database transaction after each test | Keeps tests isolated and repeatable | Test fixtures require careful transaction configuration | Yes |
| D-016 | Seed five doctors and sample patients through an idempotent script | Makes the deployed API immediately testable without duplicate records on restart | Seeded names act as stable identifiers for setup purposes | Yes |
| D-017 | Test database constraints directly | Proves that data integrity does not rely only on API validation | These tests are tied to PostgreSQL behaviour | Yes |
| D-018 | Use HTTPX2 for FastAPI and Starlette test clients | Starlette has deprecated ordinary HTTPX support for TestClient | HTTPX2 is newer and less familiar than HTTPX | Yes |
| D-019 | Run CI against a PostgreSQL service container | Ensures pull requests verify PostgreSQL-specific migrations and constraints | CI takes longer than tests using an in-memory database | Yes |
| D-020 | Use the same Python version locally and in CI | Reduces version-specific differences between development and automated tests | Upgrading Python requires updating the pinned version intentionally | Yes |
| D-021 | Verify Alembic migrations before running tests in CI | Detects broken or incomplete migrations separately from ORM table creation | Adds an additional CI step | Yes |
| D-022 | Generate slots relative to each working-period start | Supports schedules beginning at times such as 08:15 rather than assuming only :00 and :30 boundaries | Different working periods can produce different slot alignments | Yes |
| D-023 | Require timezone-aware appointment timestamps | Prevents ambiguous comparisons and avoids interpreting client-local times silently | API clients must include an offset such as +03:00 | Yes |
| D-024 | Normalize appointment times to Africa/Nairobi | Provides one consistent clinic-time basis for schedules, booking rules, and responses | Multi-timezone clinics would require configurable clinic locations | Yes |
| D-025 | Allow appointments exactly at the minimum-notice boundary | “Within one hour” is interpreted as less than 60 minutes, so exactly 60 minutes is valid | A stricter clinic policy would require changing the comparison | Yes |
| D-026 | Keep scheduling rules independent of FastAPI | Allows booking and rescheduling to reuse and test the same logic without HTTP dependencies | Endpoints must translate domain errors into HTTP responses | Yes |
| D-027 | Inject the current time through a FastAPI dependency | Makes time-sensitive API tests deterministic without changing production behaviour | Adds one application dependency to each time-sensitive endpoint | Yes |
| D-028 | Use a custom structured API error format | Gives clients and support engineers stable error codes and readable messages | FastAPI's default request-validation errors remain in their standard 422 format | Yes |
| D-029 | Perform both application conflict checks and database enforcement | Provides friendly errors while retaining concurrency-safe PostgreSQL protection | The application performs one additional conflict query before insertion | Yes |
| D-030 | Return calculated appointment end time without storing it | Keeps the database model consistent with the fixed 30-minute duration | Variable-duration appointments would require a future schema change | Yes |
| D-031 | Reject unknown appointment request properties | Detects client mistakes rather than silently ignoring unsupported input | Clients must remove any unrecognized fields | Yes |
| D-032 | Reject availability requests for past dates | Past appointment availability has no actionable booking value | Historical schedule reporting would require a separate endpoint | Yes |
| D-033 | Return an empty availability list on non-working days | The doctor exists but has no valid slots for that date | Clients must distinguish an empty schedule from a missing doctor | Yes |
| D-034 | Query only scheduled appointments when calculating availability | Cancelled appointments must release their former slots | Future blocking statuses would need to be added explicitly | Yes |
| D-035 | Calculate database day boundaries using Africa/Nairobi | Ensures appointments are matched to the clinic's local date | Multi-location clinics would require location-specific timezones | Yes |

## Independent Decisions

Two meaningful implementation decisions will be made personally by Emmanuel without first requesting an AI recommendation. They will be recorded here honestly for the assessment reflection.
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
| D-036 | Require a cancellation reason | Creates an operational record explaining why a slot was released | Clients must provide a meaningful reason before cancellation succeeds | Yes |
| D-037 | Lock an appointment row during cancellation | Prevents simultaneous requests from both acting on stale appointment state | Concurrent updates to the same appointment wait for the active transaction | Yes |
| D-038 | Preserve cancelled appointments instead of deleting them | Maintains an audit trail while the partial unique index releases the slot | Cancelled records increase table size over time | Yes |
| D-039 | Reject repeated cancellation with 409 Conflict | The request conflicts with the appointment's current state | Cancellation is not treated as silently idempotent | Yes |
| D-040 | Lock the appointment row during rescheduling | Prevents cancellation or another reschedule from concurrently modifying the same appointment | Competing operations on the same appointment wait for the transaction to finish | Yes |
| D-041 | Validate the destination before changing the appointment | Keeps the original slot unchanged when the proposed time is invalid | Validation performs database queries before the update | Yes |
| D-042 | Reject rescheduling to the current appointment time | Prevents meaningless state changes and misleading success responses | Clients receive 409 instead of an idempotent success | Yes |
| D-043 | Reuse the booking validation service for rescheduling | Ensures booking and rescheduling enforce identical schedule, notice, and timezone rules | Future operation-specific rules must be layered around the shared validator | Yes |
| D-044 | Return the previous and new appointment times | Makes the outcome explicit for API clients and support investigations | The previous time is not yet stored as permanent audit history | Yes |
| D-045 | Return only scheduled upcoming patient appointments | The endpoint is designed for actionable future bookings rather than appointment history | Cancelled and past appointments require a future history endpoint | Yes |
| D-046 | Include doctor name and specialty in patient appointment responses | Allows clients to display useful appointment information without additional doctor requests | The response duplicates a small amount of doctor data | Yes |
| D-047 | Order patient appointments by start time and ID | Produces deterministic chronological results | Same-time appointments are ordered by database identifier | Yes |
| D-048 | Return an empty list when a patient has no upcoming appointments | The patient exists successfully but has no matching records | Clients must distinguish an empty list from a missing patient | Yes |
| D-049 | Keep a separate committed-session fixture for concurrency tests | Independent database connections must see committed setup records, while ordinary tests benefit from fast rollback isolation | Concurrency tests require explicit cleanup of committed rows | Yes |
| D-050 | Use one SQLAlchemy session per worker thread | Sessions are mutable transaction objects and must not be shared across concurrent threads | Concurrent tests open additional pooled database connections | Yes |
| D-051 | Synchronize the competing transactions immediately before commit | Forces both bookings past the application conflict check and exercises PostgreSQL as the final concurrency safeguard | The test temporarily monkeypatches `Session.commit` inside one isolated test | Yes |
| D-052 | Verify both the service result and final database row count | Confirms that clients receive a useful conflict and that only one scheduled record exists | The test performs an additional verification query | Yes |
| D-053 | Assign a request ID to every HTTP request | Allows API responses and server logs to be correlated during debugging | Clients may receive a generated identifier when they do not provide one | Yes |
| D-054 | Preserve valid client-provided request IDs | Supports tracing across calling systems while limiting identifiers to 128 characters | The service trusts reasonable identifiers supplied through the header | Yes |
| D-055 | Emit JSON application logs | Produces machine-readable logs suitable for hosted log viewers and future aggregation | Human readers see one compact JSON object per line | Yes |
| D-056 | Exclude request bodies and query values from access logs | Reduces the risk of exposing patient or booking information through operational logs | Some debugging details require reproduction rather than log inspection | Yes |
| D-057 | Standardize request-validation errors | Gives malformed requests the same machine-readable error structure as domain errors | This replaces FastAPI's default `detail` response structure | Yes |
| D-058 | Define Render infrastructure in `render.yaml` | Keeps the service, database, environment variables, health check, and deployment behaviour reviewable in version control | Render-specific configuration creates some platform coupling | Yes |
| D-059 | Normalize generic PostgreSQL URLs to the Psycopg 3 SQLAlchemy scheme | Render provides a standard `postgresql://` connection string while the application uses Psycopg 3 explicitly | Configuration contains a small platform-compatibility transformation | Yes |
| D-060 | Run migrations and the idempotent seed before starting the free web service | Free Render web services lack shell access and paid pre-deploy commands, so startup must prepare the database automatically | Startup takes slightly longer and this approach is intended for the single-instance assessment deployment | Yes |
| D-061 | Deploy the web service and database in Frankfurt | Keeps both resources in one Render region and enables private-network database communication | The region cannot be changed after resource creation without recreating resources | Yes |
| D-062 | Trigger automatic deployment only after CI checks pass | Prevents a failing `main` commit from being automatically released | Deployment waits for GitHub Actions to complete | Yes |
| D-063 | Block public connections to the production database | The application only needs the internal Render connection string | Direct database inspection from a local machine is unavailable | Yes |

## Independent Decisions

Two meaningful implementation decisions will be made personally by Emmanuel without first requesting an AI recommendation. They will be recorded here honestly for the assessment reflection.
# Clinic Booking API

[![CI](https://github.com/Gambi204/clinic-booking-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Gambi204/clinic-booking-api/actions/workflows/ci.yml)

A production-minded REST API for managing doctor availability and patient appointments in a small clinic. It was built for the Savannah Informatics Backend Developer Take-Home Assessment.

## Live API

- **Base URL:** [https://clinic-booking-api-emmanuel-riungu.onrender.com](https://clinic-booking-api-emmanuel-riungu.onrender.com)
- **Swagger UI:** [Interactive API documentation](https://clinic-booking-api-emmanuel-riungu.onrender.com/docs)
- **ReDoc:** [Alternative API documentation](https://clinic-booking-api-emmanuel-riungu.onrender.com/redoc)
- **Health check:** [Service and database health](https://clinic-booking-api-emmanuel-riungu.onrender.com/health)

> The deployment uses Render's free tier. The service can take about a minute to wake after being idle, and the free PostgreSQL database is time-limited. See [Deployment limitations](#deployment-limitations).

## Assessment Requirement Coverage

| Requirement | Implementation |
|---|---|
| Book an appointment | `POST /appointments` |
| View a doctor's availability | `GET /doctors/{doctor_id}/availability` |
| Cancel an appointment | `PATCH /appointments/{appointment_id}/cancel` |
| Reschedule an appointment | `PATCH /appointments/{appointment_id}/reschedule` |
| Five doctors with fixed 30-minute slots | Idempotent seed data and configurable working periods |
| Prevent double-booking | Application conflict checks plus a PostgreSQL partial unique index |
| Meaningful validation and errors | Structured `400`, `404`, `409`, and `422` responses |
| Modular implementation | Separate routes, schemas, services, models, configuration, and middleware |
| Basic automated tests | PostgreSQL-backed service, API, constraint, concurrency, and observability tests |
| Bonus: upcoming patient appointments | `GET /patients/{patient_id}/appointments` |
| Bonus: prevent bookings within one hour | Configurable 60-minute minimum notice rule |
| Public cloud deployment | Render web service and PostgreSQL database |
| Tests on pull requests | GitHub Actions |
| Automatic deployment after merge | Render deploys `main` only after checks pass |
| AI-use transparency | Detailed AI usage log and engineering decision log |

## Key Features

- Timezone-aware scheduling in `Africa/Nairobi`.
- Fixed 30-minute appointment slots generated from each doctor's actual working-period start.
- Support for multiple working periods per day, including lunch breaks.
- One-hour minimum booking notice, with exactly 60 minutes accepted.
- Soft cancellation with a reason and timestamp.
- Atomic rescheduling with row locking and rollback protection.
- Scheduled appointments block slots; cancelled appointments release them.
- PostgreSQL-enforced protection against simultaneous double-booking.
- Upcoming patient appointments ordered chronologically.
- Request IDs, structured JSON logs, and consistent error responses.
- Idempotent seed data, Alembic migrations, CI, and public deployment.

## Technology Stack

- Python 3.14.3
- FastAPI
- PostgreSQL 18
- SQLAlchemy 2
- Psycopg 3
- Alembic
- Pydantic Settings
- pytest and pytest-cov
- GitHub Actions
- Render

## API Conventions and Scheduling Rules

- Appointment timestamps must be timezone-aware ISO 8601 values, for example `2026-07-27T10:00:00+03:00`.
- All scheduling decisions are normalized to `Africa/Nairobi`.
- Every appointment lasts 30 minutes.
- A booking must be at least 60 minutes in the future.
- The requested start must match a generated slot inside the doctor's working hours.
- The doctor must exist and be active.
- Only appointments with status `scheduled` block availability.
- A non-working day returns an empty availability list.
- Availability cannot be requested for a past date.
- Appointment end times are calculated from the fixed duration rather than stored.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Service information |
| `GET` | `/health` | API and database health |
| `POST` | `/appointments` | Create an appointment |
| `GET` | `/doctors/{doctor_id}/availability?date=YYYY-MM-DD` | List available doctor slots |
| `PATCH` | `/appointments/{appointment_id}/cancel` | Cancel and release a slot |
| `PATCH` | `/appointments/{appointment_id}/reschedule` | Move an appointment atomically |
| `GET` | `/patients/{patient_id}/appointments` | List upcoming scheduled appointments |

### Create an Appointment

```http
POST /appointments
Content-Type: application/json
```

```json
{
  "doctor_id": 1,
  "patient_id": 1,
  "start_at": "2026-07-27T10:00:00+03:00"
}
```

Successful response: `201 Created`

```json
{
  "id": 1,
  "doctor_id": 1,
  "patient_id": 1,
  "start_at": "2026-07-27T10:00:00+03:00",
  "end_at": "2026-07-27T10:30:00+03:00",
  "status": "scheduled",
  "created_at": "2026-07-25T18:20:00+03:00"
}
```

### Get Doctor Availability

```http
GET /doctors/1/availability?date=2026-07-27
```

```json
{
  "doctor_id": 1,
  "doctor_name": "Dr. Amina Hassan",
  "date": "2026-07-27",
  "timezone": "Africa/Nairobi",
  "slot_duration_minutes": 30,
  "available_slots": [
    {
      "start_at": "2026-07-27T08:00:00+03:00",
      "end_at": "2026-07-27T08:30:00+03:00"
    }
  ]
}
```

### Cancel an Appointment

```http
PATCH /appointments/1/cancel
Content-Type: application/json
```

```json
{
  "reason": "Patient is no longer available."
}
```

Cancellation preserves the appointment record, records the reason and cancellation time, and immediately releases the slot.

### Reschedule an Appointment

```http
PATCH /appointments/1/reschedule
Content-Type: application/json
```

```json
{
  "new_start_at": "2026-07-27T11:00:00+03:00"
}
```

A successful response includes both `previous_start_at` and the new `start_at`. Failed validation or an occupied destination leaves the original appointment unchanged.

### Get Upcoming Patient Appointments

```http
GET /patients/1/appointments
```

The endpoint returns only scheduled appointments at or after the current clinic time, ordered from earliest to latest. Each item includes the doctor's name and specialty.

## Error Responses

Handled API errors use a consistent envelope:

```json
{
  "error": {
    "code": "SLOT_UNAVAILABLE",
    "message": "The requested appointment slot is no longer available.",
    "request_id": "frontend-request-12345"
  }
}
```

Common status codes:

| Status | Meaning |
|---|---|
| `400 Bad Request` | A scheduling or business rule was violated |
| `404 Not Found` | A doctor, patient, or appointment does not exist |
| `409 Conflict` | The requested operation conflicts with current state |
| `422 Unprocessable Entity` | The request structure or field values are invalid |

Representative error codes include:

- `DOCTOR_NOT_FOUND`
- `PATIENT_NOT_FOUND`
- `APPOINTMENT_NOT_FOUND`
- `DOCTOR_INACTIVE`
- `TIMEZONE_REQUIRED`
- `APPOINTMENT_NOT_IN_FUTURE`
- `MINIMUM_NOTICE_NOT_MET`
- `DOCTOR_NOT_WORKING`
- `INVALID_APPOINTMENT_SLOT`
- `SLOT_UNAVAILABLE`
- `APPOINTMENT_ALREADY_CANCELLED`
- `CANCELLED_APPOINTMENT_CANNOT_BE_RESCHEDULED`
- `APPOINTMENT_TIME_UNCHANGED`
- `AVAILABILITY_DATE_IN_PAST`
- `REQUEST_VALIDATION_ERROR`

## Architecture

Business rules are kept outside the HTTP layer so that booking, availability, cancellation, and rescheduling reuse the same scheduling logic.

```text
app/
├── api/            # FastAPI routers and API error handling
├── core/           # Settings, clock, and logging
├── db/             # SQLAlchemy base, engine, sessions, and dependencies
├── middleware/     # Request-ID and request logging middleware
├── models/         # SQLAlchemy domain models
├── schemas/        # Pydantic request and response models
├── services/       # Scheduling and appointment business logic
├── main.py         # Application entry point
└── seed.py         # Idempotent demonstration data

alembic/            # Database migrations
tests/              # PostgreSQL-backed automated tests
docs/               # Decisions, AI log, specifications, and verification
.github/workflows/  # Pull-request and main-branch CI
render.yaml         # Render Blueprint
```

## Data Integrity and Concurrency

The system uses two layers of double-booking protection:

1. The service checks for an existing scheduled appointment and returns a clear `SLOT_UNAVAILABLE` error.
2. PostgreSQL enforces a partial unique index on `(doctor_id, start_at)` for rows whose status is `scheduled`.

The test suite includes a real two-transaction race test. Both workers observe the slot as free before attempting to commit. PostgreSQL allows one transaction to succeed and rejects the other, leaving exactly one scheduled appointment.

Cancellation and rescheduling use row locks to avoid simultaneous operations acting on stale appointment state.

## Local Setup

### Prerequisites

- Python 3.14.3
- PostgreSQL 18
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Gambi204/clinic-booking-api.git
cd clinic-booking-api
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Create development and test databases

Create two PostgreSQL databases, for example:

```text
clinic_booking_db
clinic_booking_test_db
```

Use a dedicated PostgreSQL role with access to both databases.

### 5. Configure environment variables

Copy the example file:

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Set at least:

```env
APP_NAME=Clinic Booking API
APP_VERSION=1.0.0
APP_ENV=development

DATABASE_URL=postgresql+psycopg://<user>:<password>@localhost:5432/clinic_booking_db
TEST_DATABASE_URL=postgresql+psycopg://<user>:<password>@localhost:5432/clinic_booking_test_db

CLINIC_TIMEZONE=Africa/Nairobi
SLOT_DURATION_MINUTES=30
MIN_BOOKING_NOTICE_MINUTES=60
```

The private `.env` file is ignored by Git and must never be committed.

### 6. Apply migrations

```bash
alembic upgrade head
alembic current
```

### 7. Seed demonstration data

```bash
python -m app.seed
```

The seed is idempotent and creates five doctors, their working periods, and three sample patients without duplicating existing seed records.

### 8. Start the API

```bash
python -m uvicorn app.main:app --reload
```

Open:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`
- `http://127.0.0.1:8000/health`

## Testing

The test suite runs against PostgreSQL rather than SQLite so PostgreSQL-specific constraints, partial indexes, locking, and transaction behavior are tested directly.

Run all tests:

```bash
python -m pytest -v
```

Run with coverage:

```bash
python -m pytest --cov=app --cov-report=term-missing
```

The suite covers:

- Root and database health endpoints.
- Database constraints and migrations.
- Slot generation, breaks, alignment, and timezone conversion.
- Minimum-notice and past-time validation.
- Booking success and failure paths.
- Availability filtering.
- Cancellation and slot release.
- Atomic rescheduling and rollback behavior.
- Upcoming patient appointment ordering and filtering.
- A genuine simultaneous-booking race.
- Request-ID generation and propagation.
- Structured domain and validation errors.
- JSON log formatting.
- Render database URL normalization.

## Continuous Integration and Delivery

GitHub Actions runs on:

- Every pull request targeting `main`.
- Every push to `main`.

The workflow:

1. Starts a PostgreSQL 18 service container.
2. Installs the pinned Python dependencies.
3. Applies and verifies Alembic migrations.
4. Runs the complete pytest suite with coverage.

Render is configured through `render.yaml` and automatically deploys `main` only after linked checks pass.

## Observability

Every response includes an `X-Request-ID` header. A valid client-supplied ID is preserved; otherwise, the API generates a UUID.

Application request logs are emitted as JSON and include:

- Request ID
- HTTP method
- Request path
- Status code
- Duration in milliseconds
- Client address

Request bodies, query-string values, patient details, email addresses, and phone numbers are intentionally excluded from application request logs.

## Deployment

The repository's `render.yaml` Blueprint defines:

- A Python web service.
- A PostgreSQL 18 database.
- Private database connectivity.
- A database-aware `/health` check.
- Environment variables.
- CI-gated automatic deployment from `main`.

Build command:

```bash
python -m pip install --upgrade pip &&
python -m pip install -r requirements.txt
```

Start command:

```bash
alembic upgrade head &&
python -m app.seed &&
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Migrations and the idempotent seed run before Uvicorn starts, making a new assessment environment immediately testable.

### Deployment Limitations

The public demonstration uses Render free resources:

- The web service spins down after 15 minutes without inbound traffic and may take about one minute to wake.
- The free PostgreSQL database expires 30 days after creation.
- Free PostgreSQL does not provide backups or managed connection pooling.
- The deployment is intended for assessment demonstration, not long-term production use.

## Documentation

- [Project specification](docs/PROJECT_SPEC.md)
- [Data model](docs/DATA_MODEL.md)
- [Engineering decision log](docs/DECISIONS.md)
- [AI usage log and reflection](docs/AI_USAGE_LOG.md)
- [Deployment verification](docs/DEPLOYMENT_VERIFICATION.md)
- [Render Blueprint](render.yaml)

## AI Usage and Candidate Responsibility

AI was used as a development assistant for planning, implementation suggestions, testing ideas, troubleshooting, and documentation structure.

All AI-assisted output was reviewed, understood, run, and tested before acceptance. Incorrect or incomplete suggestions were recorded rather than hidden. The candidate remains responsible for the final architecture, implementation, verification, and submission.

The detailed record is available in [docs/AI_USAGE_LOG.md](docs/AI_USAGE_LOG.md). Key architectural choices and trade-offs are documented in [docs/DECISIONS.md](docs/DECISIONS.md).

## Limitations and Possible Improvements

For a larger production system, the next improvements would include:

- Authentication and role-based authorization.
- Patient and doctor management endpoints.
- Permanent appointment-change audit history.
- Database-level prevention of overlapping working-hour periods.
- Rate limiting and abuse protection.
- Pagination for patient appointment results.
- Production backups, connection pooling, and an always-on service tier.
- Metrics, alerting, and centralized log aggregation.

## Candidate

**Emmanuel Mugambi Riungu**

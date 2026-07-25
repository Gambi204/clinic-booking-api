# Clinic Booking API

A production-minded REST API for managing doctor availability and patient appointments in a small clinic.

This project is being developed as part of the Savannah Informatics Backend Developer Take-Home Assessment.

## Current Status

Completed:

- FastAPI application foundation.
- PostgreSQL and SQLAlchemy configuration.
- Alembic migrations.
- Doctor, working-hours, patient, and appointment models.
- PostgreSQL double-booking constraint.
- Idempotent seed data.
- PostgreSQL-backed automated tests.
- Pull-request CI using GitHub Actions.
- Timezone-aware slot generation and appointment-time validation.
- Appointment creation endpoint with structured error handling.
- Doctor availability endpoint with scheduled-slot filtering.
- Appointment cancellation with row locking and immediate slot release.
- Atomic appointment rescheduling with destination validation and rollback protection.
- Bonus endpoint for upcoming patient appointments.

## Technology Stack

* Python 3.14
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* pytest
* GitHub Actions
* Render

## Documentation

Interactive Swagger API documentation is available at:

```text
/docs
```

A secondary ReDoc interface is available at:

```text
/redoc
```

## Current Endpoints

* `GET /`
* `GET /health`
* `POST /appointments`
* `GET /doctors/{doctor_id}/availability?date=YYYY-MM-DD`
* `PATCH /appointments/{appointment_id}/cancel`
* `PATCH /appointments/{appointment_id}/reschedule`
* `GET /patients/{patient_id}/appointments`

### Create an Appointment

```http
POST /appointments
```

### Get Doctor Availability

```http
GET /doctors/{doctor_id}/availability?date=2026-07-27
```

### Cancel an Appointment

```http
PATCH /appointments/{appointment_id}/cancel
```

### Reschedule an Appointment

```http
PATCH /appointments/{appointment_id}/reschedule
```
### Get Upcoming Patient Appointments

```http
GET /patients/{patient_id}/appointments
```

The endpoint returns upcoming scheduled appointments ordered from earliest to latest.

Each result includes:

- Appointment identifier.
- Doctor identifier.
- Doctor name and specialty.
- Start time.
- Calculated end time.
- Appointment status.

Past and cancelled appointments are excluded.

Possible handled errors include:

- `PATIENT_NOT_FOUND`

### Concurrency Protection

The test suite includes a PostgreSQL-backed simultaneous-booking
test. Two independent transactions attempt to reserve the same
doctor and start time after both have observed the slot as available.

The test verifies that:

- Exactly one transaction succeeds.
- The competing transaction receives `SLOT_UNAVAILABLE`.
- Exactly one scheduled appointment exists in PostgreSQL.
- The partial unique index remains the final double-booking safeguard.

## Observability

Every API response includes an `X-Request-ID` header.

Clients may supply an identifier:

```http
X-Request-ID: frontend-request-12345
```

When no valid identifier is supplied, the API generates a UUID.

Handled API errors include the same identifier:

```json
{
  "error": {
    "code": "PATIENT_NOT_FOUND",
    "message": "Patient 999 was not found.",
    "request_id": "frontend-request-12345"
  }
}
```

Application request logs are emitted as JSON and include:

- Request ID
- HTTP method
- Request path
- Status code
- Duration in milliseconds
- Client address

Request bodies, query values, patient details, emails, and phone
numbers are not included in application request logs.

## Seed Data

The development database can be populated with five doctors, their working hours, and three sample patients by running:

```bash
python -m app.seed
```

The seed operation is idempotent. It can be executed repeatedly without creating duplicate doctors, working-hour periods, or patients.

## Running Tests

Create a separate PostgreSQL test database and configure `TEST_DATABASE_URL` in the local `.env` file.

Run the complete test suite:

```bash
python -m pytest -v
```

Run the tests with a terminal coverage report:

```bash
python -m pytest --cov=app --cov-report=term-missing
```

The tests use PostgreSQL rather than SQLite so that PostgreSQL-specific constraints, partial indexes, and transaction behaviour are exercised accurately.

- Request-ID generation and propagation.
- Structured domain and request-validation errors.
- JSON request-log formatting.

## Database Migrations

Apply all available migrations:

```bash
alembic upgrade head
```

View the currently applied migration:

```bash
alembic current
```

Reverse the latest migration:

```bash
alembic downgrade -1
```

## Local Development Server

Start the application locally with:

```bash
python -m uvicorn app.main:app --reload
```

The application will be available at:

```text
http://127.0.0.1:8000
```

The Swagger interface will be available at:

```text
http://127.0.0.1:8000/docs
```

## Environment Variables

Copy `.env.example` to `.env` and configure the required database connection values.

The main environment variables are:

* `DATABASE_URL`
* `TEST_DATABASE_URL`
* `APP_NAME`
* `APP_ENV`
* `CLINIC_TIMEZONE`
* `SLOT_DURATION_MINUTES`
* `MIN_BOOKING_NOTICE_MINUTES`

The `.env` file contains local secrets and must not be committed to Git.

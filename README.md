# Clinic Booking API

A production-minded REST API for managing doctor availability and patient appointments in a small clinic.

This project is being developed as part of the Savannah Informatics Backend Developer Take-Home Assessment.

## Current Status

The project foundation, PostgreSQL database configuration, SQLAlchemy models, Alembic migrations, seed data, and initial automated tests have been completed.

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

Additional appointment-management endpoints are under development.

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

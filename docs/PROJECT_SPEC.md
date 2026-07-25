# Clinic Booking API — Project Specification

## Source

Savannah Informatics Backend Developer Take-Home Assessment.

## Confirmed Requirements

### Required endpoints

- `POST /appointments`
- `GET /doctors/{id}/availability`
- `PATCH /appointments/{id}/cancel`
- `PATCH /appointments/{id}/reschedule`

### Required booking rules

- Appointments must fall within the doctor's working hours.
- Appointments must not be in the past.
- A booked slot must not be available to another patient.
- Slots have a fixed duration of 30 minutes.
- Cancelling an appointment must release its slot.
- Cancelling an already cancelled appointment must return an error.
- Rescheduling must validate the new slot like a fresh booking.
- Rescheduling must release the original slot.
- A cancelled appointment cannot be rescheduled.
- Validation failures must use meaningful messages and appropriate HTTP status codes.
- The code must be split into sensible modules.
- Booking logic must have automated test coverage.

### Bonus requirements

- `GET /patients/{id}/appointments`
- Return upcoming appointments sorted by date.
- Prevent booking appointments within one hour of the current time.

### Deployment requirements

- Public cloud deployment.
- Publicly reachable application at submission time.
- Tests run on every pull request.
- Merging a pull request into the designated branch deploys automatically.
- README explains the deployment branch and CI/CD process.

### Documentation requirements

- System design.
- Models and components.
- Key decisions.
- Trade-offs.
- Local setup instructions.
- Public deployment URL.
- CI/CD explanation.
- AI reflection.

## Locked Technical Decisions

- Framework: FastAPI.
- Database: PostgreSQL.
- ORM: synchronous SQLAlchemy.
- Migrations: Alembic.
- Tests: pytest.
- CI/CD: GitHub Actions.
- Hosting: Render free tier.
- Deployment branch: `main`.
- Clinic timezone: `Africa/Nairobi`.
- Appointment duration: 30 minutes.
- API documentation: FastAPI OpenAPI/Swagger.
- Double-booking protection: application validation plus a PostgreSQL constraint.
- Rescheduling: atomic database transaction.
- Cost target: $0.

## Deliberately Out of Scope

- Frontend application.
- Authentication and authorization.
- Payments.
- Email or SMS reminders.
- Prescriptions and medical records.
- Microservices.
- Redis or background workers.
- Kubernetes.
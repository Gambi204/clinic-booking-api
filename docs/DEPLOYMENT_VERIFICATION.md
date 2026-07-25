# Deployment Verification

## Environment

- Platform: Render
- Region: Frankfurt
- Runtime: Python 3.14.3
- Database: PostgreSQL 18
- Clinic timezone: Africa/Nairobi
- Deployment branch: main
- Public base URL: `https://clinic-booking-api-emmanuel-riungu.onrender.com`

## Deployment Checks

- [x] Render Blueprint created the web service and PostgreSQL database.
- [x] Build completed successfully.
- [x] Alembic migrated the production database.
- [x] The idempotent seed completed.
- [x] `/health` returned `200` with the database reachable.
- [x] Swagger and ReDoc loaded publicly.
- [x] Request IDs appeared in response headers and application logs.
- [x] Doctor availability returned seeded working-hour slots.
- [x] Appointment creation returned `201`.
- [x] Duplicate booking returned `409 SLOT_UNAVAILABLE`.
- [x] Patient upcoming appointments returned the created booking.
- [x] Rescheduling released the original slot and occupied the new slot.
- [x] Cancellation released the rescheduled slot.
- [x] GitHub Actions passed before deployment.

## Free-Tier Limitations

The public demonstration uses Render free resources.

- The web service can spin down after inactivity.
- The first request after inactivity can be delayed while it starts.
- The free PostgreSQL database expires 30 days after creation.
- The deployment is intended for assessment demonstration rather than
  long-term production use.
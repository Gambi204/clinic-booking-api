# Data Model

## Doctor

Represents a doctor whose schedule can be booked.

Key fields:

- `id`
- `full_name`
- `specialty`
- `is_active`
- `created_at`
- `updated_at`

A doctor has many working-hour periods and many appointments.

## DoctorWorkingHours

Represents one period during which a doctor accepts appointments.

Key fields:

- `doctor_id`
- `weekday`
- `start_time`
- `end_time`

Weekdays use Python numbering:

- Monday = 0
- Sunday = 6

A doctor can have multiple periods on one day, allowing breaks between periods.

## Patient

Represents a patient who can make appointments.

Key fields:

- `full_name`
- `email`
- `phone_number`

Email addresses are unique in the current system.

## Appointment

Represents a fixed 30-minute appointment between a doctor and patient.

Key fields:

- `doctor_id`
- `patient_id`
- `start_at`
- `status`
- `cancellation_reason`
- `cancelled_at`

Valid statuses are:

- `scheduled`
- `cancelled`

The appointment end time is calculated as 30 minutes after `start_at`.

## Double-Booking Protection

The application will check slot availability before inserting an appointment.

PostgreSQL also enforces a partial unique index on:

- `doctor_id`
- `start_at`

The index applies only when the appointment status is `scheduled`.

This prevents concurrent requests from creating two scheduled appointments for the same doctor and time while allowing cancelled historical records to remain stored.

## Deletion Rules

- Deleting a doctor removes their working-hour records.
- Doctors and patients with appointment history cannot be deleted through ordinary foreign-key cascading.
- Appointments are cancelled rather than deleted.
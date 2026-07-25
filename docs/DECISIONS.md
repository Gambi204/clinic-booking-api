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

## Independent Decisions

Two meaningful implementation decisions will be made personally by Emmanuel without first requesting an AI recommendation. They will be recorded here honestly for the assessment reflection.
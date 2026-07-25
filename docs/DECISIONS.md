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

## Independent Decisions

Two meaningful implementation decisions will be made personally by Emmanuel without first requesting an AI recommendation. They will be recorded here honestly for the assessment reflection.
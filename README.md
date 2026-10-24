# WP CRM Service

A simulated CRM backend built with Python, FastAPI, and SQLite to receive and store leads from the WP CRM Bridge WordPress plugin.

## Features

- FastAPI REST endpoints
- API key authentication
- Pydantic request validation
- SQLite lead persistence
- Duplicate lead detection
- Conflict handling for reused references
- Automated API tests with pytest

## Architecture

`WordPress Plugin → Authenticated HTTP Request → FastAPI → SQLite`

Each lead contains a unique external reference, name, email, and message.

The service uses the external reference to distinguish new submissions from duplicate or conflicting submissions.

## Technology Stack

- Python
- FastAPI
- Pydantic
- SQLite
- pytest
- Uvicorn

## Local Setup

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure the required API key in a local `.env` file.
5. Start the development server:

```bash
python -m uvicorn app.main:app --reload
```

6. Open the API documentation at:

`http://127.0.0.1:8000/docs`

## API Endpoints

### GET /health

Returns the service health status.

### POST /api/leads

Receives a lead from an authenticated client.

The request requires an `X-API-Key` header and a valid JSON payload.

Example payload:

```json
{
  "reference": "WP-LOCAL-CRM-000006",
  "name": "Olivia Morgan",
  "email": "olivia@example.com",
  "message": "Interested in CRM integration."
}
```

## Duplicate Handling

Lead references are unique.

The service distinguishes between:

- New lead submissions
- Repeated submissions containing matching data
- Conflicting submissions that reuse a reference with different data

This helps prevent duplicate CRM records during delivery retries.

## Automated Testing

Run:

```bash
python -m pytest -v
```

The test suite covers API health, authentication, lead creation, and persistence behavior.

## Security

- API key authentication
- Request validation
- Parameterized SQLite queries
- Unique lead references
- Environment-based configuration

This is a local development service, not a production CRM platform.

## Development Status

Local API implementation, automated tests, and WordPress integration testing completed.

This service acts as a development and testing CRM for WP CRM Bridge. Future versions of the WordPress plugin may support standalone enquiry management and additional CRM providers without requiring this Python service.
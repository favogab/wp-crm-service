
"""
WP CRM Bridge — Simulated CRM Service.

This FastAPI application receives leads from external clients.
For now, records are stored in memory so we can test HTTP
communication before introducing authentication and persistence.
"""


import os
import secrets

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Response, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, EmailStr, Field

# Load local environment variables before configuring the service.
load_dotenv()

CRM_API_KEY = os.getenv("CRM_API_KEY")

if not CRM_API_KEY:
    raise RuntimeError("CRM_API_KEY is missing from environment configuration.")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Security(api_key_header)):
    """Reject requests without the configured shared API key."""

    if not api_key or not secrets.compare_digest(api_key, CRM_API_KEY):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key."
        )


app = FastAPI(
    title="WP CRM Bridge — CRM Service",
    version="0.1.0",
)

@app.get("/health")
def health_check():
    """Return a simple response to confirm the CRM API is running."""
    return {"status": "healthy"}


class Lead(BaseModel):
    """Define and validate the structure of an incoming lead."""

    reference: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    message: str = Field(min_length=1, max_length=5000)


# Temporary development storage.
# Records disappear whenever the Python process restarts.
received_leads = {}



@app.post(
    "/api/leads",
    status_code=201,
    dependencies=[Depends(verify_api_key)]
)
def receive_lead(lead: Lead, response: Response):
    """Accept an authenticated lead without creating duplicates."""

    if lead.reference in received_leads:
        # Repeated delivery of the same reference is acknowledged.
        # We will add payload-conflict detection in a later session.
        response.status_code = 200

        return {
            "success": True,
            "message": "Lead already received.",
            "reference": lead.reference,
        }

    received_leads[lead.reference] = lead.model_dump(mode="json")

    return {
        "success": True,
        "message": "Lead received successfully.",
        "reference": lead.reference,
    }



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

from contextlib import asynccontextmanager
from fastapi import HTTPException

from app.database import (
    initialize_database,
    save_lead,
)

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize persistent storage when FastAPI starts."""

    initialize_database()

    yield


app = FastAPI(
    title="WP CRM Bridge — CRM Service",
    version="0.1.0",
    lifespan=lifespan,
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


@app.post(
    "/api/leads",
    status_code=201,
    dependencies=[Depends(verify_api_key)],
)


def receive_lead(lead: Lead, response: Response):
    """Store a lead and return an accurate delivery result."""

    result = save_lead(lead)

    if result == "duplicate":
        # A retry of an already stored lead is successful.
        response.status_code = 200

        return {
            "success": True,
            "message": "Lead already received.",
            "reference": lead.reference,
        }

    if result == "conflict":
        # Never silently replace an existing CRM record.
        raise HTTPException(
            status_code=409,
            detail="Lead reference exists with different data.",
        )

    # A genuinely new record was created.
    return {
        "success": True,
        "message": "Lead stored successfully.",
        "reference": lead.reference,
    }
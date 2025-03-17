from fastapi import FastAPI, Request, Depends, HTTPException
import httpx
import os
from typing import Optional
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI()

# OpenSearch configuration
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
OPENSEARCH_PASS = os.getenv("OPENSEARCH_PASS", "admin")  # Use secrets manager for production
OPENSEARCH_API_KEY = os.getenv("OPENSEARCH_API_KEY")  # Alternative: API Key

security = HTTPBasic()  # For optional Basic Auth


async def forward_request(path: str, request: Request):
    """
    Forwards requests to OpenSearch with authentication.
    """
    url = f"{OPENSEARCH_URL}/{path}"  # Full OpenSearch URL

    # Extract query params and request body
    query_params = request.query_params
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.json()

    # HTTP Headers (forwarding + authentication)
    headers = dict(request.headers)
    
    if OPENSEARCH_API_KEY:
        headers["Authorization"] = f"ApiKey {OPENSEARCH_API_KEY}"
    else:
        headers["Authorization"] = f"Basic {httpx.auth._basic_auth_str(OPENSEARCH_USER, OPENSEARCH_PASS)}"

    # Send request to OpenSearch
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            json=body,
            params=query_params,
            headers=headers,
        )

    # Handle OpenSearch errors
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()


@app.api_route("/opensearch/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_opensearch(path: str, request: Request):
    """
    Generic FastAPI endpoint to proxy requests to OpenSearch.
    Supports authentication and dynamic requests.
    """
    return await forward_request(path, request)

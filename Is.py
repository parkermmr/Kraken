from fastapi import FastAPI, Request, HTTPException
import requests
import os
import base64
import json

app = FastAPI()

# OpenSearch configuration (set these in your environment)
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
OPENSEARCH_PASS = os.getenv("OPENSEARCH_PASS", "admin")
OPENSEARCH_API_KEY = os.getenv("OPENSEARCH_API_KEY")  # Alternative: API Key

TIMEOUT = 10  # Set request timeout in seconds


def get_auth_headers():
    """
    Generates authentication headers for OpenSearch.
    Supports Basic Auth and API Key Auth.
    """
    headers = {}
    if OPENSEARCH_API_KEY:
        headers["Authorization"] = f"ApiKey {OPENSEARCH_API_KEY}"
    else:
        # Encode Basic Auth (username:password)
        auth_string = f"{OPENSEARCH_USER}:{OPENSEARCH_PASS}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_auth}"

    return headers


def forward_request(path: str, request: Request):
    """
    Forwards requests to OpenSearch with authentication.
    Uses `requests` instead of `httpx`.
    """
    url = f"{OPENSEARCH_URL}/{path}"  # Full OpenSearch URL

    # Extract query params
    query_params = request.query_params

    # Read body only for methods that support it
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            raw_body = request.body()
            if raw_body:
                body = json.loads(raw_body.decode("utf-8"))  # Convert to JSON
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format in request body.")

    # Merge authentication headers
    headers = {**dict(request.headers), **get_auth_headers()}

    try:
        # Send request to OpenSearch
        response = requests.request(
            method=request.method,
            url=url,
            json=body,  # Only sends body if not None
            params=query_params,
            headers=headers,
            timeout=TIMEOUT,  # Avoid hanging requests
        )

        # Handle OpenSearch errors
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to OpenSearch: {str(e)}")


@app.api_route("/opensearch/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_opensearch(path: str, request: Request):
    """
    Generic FastAPI endpoint to proxy requests to OpenSearch.
    Supports authentication, query parameters, and request bodies.
    """
    return forward_request(path, request)

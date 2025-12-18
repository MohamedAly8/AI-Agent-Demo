import os
import yaml
import json
from textwrap import dedent
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from typing import List, Optional

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

tags_metadata = [
    {
        "name": "Users",
        "description": "Operations for looking up customer profiles and identity.",
    },
    {
        "name": "Orders",
        "description": "Access to purchase history and transaction details.",
    },
    {
        "name": "Support",
        "description": "Manage customer cases, incidents, and sentiment analysis.",
    },
    {
        "name": "Knowledge Base",
        "description": "Search internal policy documents (Returns, Warranty, etc.).",
    },
]

api_description = dedent("""
    ## Overview
    This API provides access to customer data, including:
    * **Profiles**: User tiers, risk scores, and contact info.
    * **Commerce**: Order history and purchase details.
    * **Support**: Past case history and sentiment analysis.
    * **Knowledge**: Internal policy documents for agent support.
""")

app = FastAPI(
    title="VaultCRM API",
    description=api_description,
    version="2.0.0",
    servers=[{"url": BASE_URL}],
    openapi_tags=tags_metadata
)

@app.on_event("startup")
def export_openapi_yaml():
    """Auto-generates openapi.yaml on server startup."""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=app.servers
    )
    
    cleaned_schema = json.loads(json.dumps(openapi_schema, default=str))

    with open("openapi.yaml", "w") as f:
        yaml.dump(cleaned_schema, f, sort_keys=False)
    print("openapi.yaml has been generated in the root directory.")

# --- Mock Data ---
USERS = {
    "alice@example.com": {
        "id": "u_101",
        "name": "Alice Smith",
        "email": "alice@example.com",
        "tier": "Platinum",
        "churn_risk": "Medium",
        "lifetime_value": 15400.00
    }
}

ORDERS = {
    "u_101": [
        {"order_id": "o_999", "item": "ErgoChair Pro", "date": "2023-09-01", "price": 450.00, "status": "Delivered"},
        {"order_id": "o_888", "item": "Gaming Monitor 4K", "date": "2023-10-20", "price": 600.00, "status": "Delivered"} 
    ]
}

CASES = {
    "u_101": [
        {"case_id": "c_202", "date": "2023-09-05", "subject": "Chair wheel stuck", "resolution": "Sent replacement wheel", "sentiment": "Neutral"},
        {"case_id": "c_205", "date": "2023-11-01", "subject": "Monitor flickering", "resolution": "Troubleshooting guide sent", "sentiment": "Negative"}
    ]
}

KNOWLEDGE_BASE = {
    "returns": "Standard return policy is 30 days from purchase. Items must be in original packaging.",
    "warranty": "Electronics have a 1-year manufacturer warranty. Platinum tier customers get an automatic 60-day return window instead of the standard 30.",
    "shipping": "Free shipping for orders over $50. Platinum members get free next-day air."
}

# --- Models (Rich Documentation) ---
class UserProfile(BaseModel):
    id: str = Field(..., description="Unique internal user ID", example="u_101")
    name: str = Field(..., description="Customer's full name", example="Alice Smith")
    tier: str = Field(..., description="Loyalty tier (Silver, Gold, Platinum)", example="Platinum")
    churn_risk: str = Field(..., description="Predicted risk of leaving (Low, Medium, High)", example="Medium")
    lifetime_value: float = Field(..., description="Total revenue from customer", example=15400.00)

class Order(BaseModel):
    order_id: str = Field(..., example="o_888")
    item: str = Field(..., example="Gaming Monitor 4K")
    date: str = Field(..., description="ISO 8601 date string", example="2023-10-20")
    price: float = Field(..., example=600.00)
    status: str = Field(..., description="Order status (Processing, Delivered, Returned)", example="Delivered")

class Case(BaseModel):
    case_id: str = Field(..., example="c_205")
    date: str = Field(..., example="2023-11-01")
    subject: str = Field(..., description="Brief summary of the issue", example="Monitor flickering")
    resolution: str = Field(..., description="Action taken by support", example="Troubleshooting guide sent")
    sentiment: str = Field(..., description="AI-analyzed sentiment of the interaction", example="Negative")

class DocSearchResult(BaseModel):
    topic: str = Field(..., description="Policy topic key", example="warranty")
    content: str = Field(..., description="Full text of the policy", example="Electronics have a 1-year manufacturer warranty...")

# --- RESTful Endpoints ---
@app.get(
    "/users", 
    response_model=UserProfile, 
    tags=["Users"],
    summary="Find User",
    description="Look up a single user by their email address.",
    operation_id="get_user_by_email"
)
async def get_user(
    email: str = Query(..., description="The email address associated with the account", example="alice@example.com")
):
    user = USERS.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get(
    "/users/{user_id}/orders", 
    response_model=List[Order],
    tags=["Orders"],
    summary="Get Order History",
    description="Retrieve all past orders for a specific user ID.",
    operation_id="get_user_orders"
)
async def get_user_orders(
    user_id: str = Path(..., description="The internal user ID (e.g., u_101)", example="u_101")
):
    return ORDERS.get(user_id, [])

@app.get(
    "/users/{user_id}/cases", 
    response_model=List[Case],
    tags=["Support"],
    summary="Get Support Cases",
    description="Retrieve history of support tickets and incidents.",
    operation_id="get_user_cases"
)
async def get_user_cases(
    user_id: str = Path(..., description="The internal user ID", example="u_101")
):
    return CASES.get(user_id, [])

@app.get(
    "/documents", 
    response_model=List[DocSearchResult],
    tags=["Knowledge Base"],
    summary="Search Knowledge Base",
    description="Search internal policies by keyword (e.g., 'warranty', 'return').",
    operation_id="search_documents"
)
async def search_documents(
    q: str = Query(..., alias="q", description="Keyword to search in policy topics and content", example="warranty")
):
    results = []
    for topic, content in KNOWLEDGE_BASE.items():
        if q.lower() in topic or q.lower() in content.lower():
            results.append({"topic": topic, "content": content})
    return results

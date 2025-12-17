import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

app = FastAPI(
    title="Enterprise CRM API",
    description="API for customer profiles, case history, orders, and internal knowledge base.",
    version="2.0.0",
    servers=[{"url": BASE_URL}]
)

# --- Mock Data ---

# 1. USERS: Rich profile data
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

# 2. ORDERS: Purchase history with dates
ORDERS = {
    "u_101": [
        {"order_id": "o_999", "item": "ErgoChair Pro", "date": "2023-09-01", "price": 450.00, "status": "Delivered"},
        {"order_id": "o_888", "item": "Gaming Monitor 4K", "date": "2023-10-20", "price": 600.00, "status": "Delivered"} 
        # Note: If today is Dec 15, Oct 20 is > 30 days ago.
    ]
}

# 3. CASES: Past incidents
CASES = {
    "u_101": [
        {"case_id": "c_202", "date": "2023-09-05", "subject": "Chair wheel stuck", "resolution": "Sent replacement wheel", "sentiment": "Neutral"},
        {"case_id": "c_205", "date": "2023-11-01", "subject": "Monitor flickering", "resolution": "Troubleshooting guide sent", "sentiment": "Negative"}
    ]
}

# 4. DOCUMENTS: Internal Knowledge Base
KNOWLEDGE_BASE = {
    "returns": "Standard return policy is 30 days from purchase. Items must be in original packaging.",
    "warranty": "Electronics have a 1-year manufacturer warranty. Platinum tier customers get an automatic 60-day return window instead of the standard 30.",
    "shipping": "Free shipping for orders over $50. Platinum members get free next-day air."
}

# --- Models ---
class UserProfile(BaseModel):
    id: str
    name: str
    tier: str
    churn_risk: str
    lifetime_value: float

class Case(BaseModel):
    case_id: str
    date: str
    subject: str
    resolution: str
    sentiment: str

class Order(BaseModel):
    order_id: str
    item: str
    date: str
    price: float
    status: str

class DocSearchResult(BaseModel):
    topic: str
    content: str

@app.get("/users/lookup", response_model=UserProfile, operation_id="lookup_user")
async def lookup_user(email: str):
    """Find a user by email to get their ID, tier, and churn risk."""
    user = USERS.get(email)
    if not user: raise HTTPException(404, "User not found")
    return user

@app.get("/users/{user_id}/orders", response_model=List[Order], operation_id="get_user_orders")
async def get_user_orders(user_id: str):
    """Get purchase history to verify item ownership and purchase dates."""
    return ORDERS.get(user_id, [])

@app.get("/users/{user_id}/cases", response_model=List[Case], operation_id="get_user_cases")
async def get_user_cases(user_id: str):
    """Retrieve past support tickets to understand the user's history and sentiment."""
    return CASES.get(user_id, [])

@app.get("/documents/search", response_model=List[DocSearchResult], operation_id="search_knowledge_base")
async def search_knowledge_base(query: str):
    """
    Search internal policy documents. 
    Useful for checking return policies, warranties, or shipping rules.
    Query should be a keyword like 'returns', 'warranty', 'shipping'.
    """
    results = []
    for topic, content in KNOWLEDGE_BASE.items():
        if query.lower() in topic or query.lower() in content.lower():
            results.append({"topic": topic, "content": content})
    return results

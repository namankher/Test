"""
Main API router for the Manufacturing RFQ Platform
"""
from fastapi import APIRouter

from app.api.api_v1.endpoints import quotes, upload, dashboard, clients, auth

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(quotes.router, prefix="/quotes", tags=["quotes"])
api_router.include_router(upload.router, prefix="/upload", tags=["file-upload"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
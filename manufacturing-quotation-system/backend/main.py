from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv

from app.api.routers import upload, analysis, quotation, feedback
from app.core.database import engine, Base

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Manufacturing Quotation System",
    description="AI-powered manufacturing quotation system for 2D/3D drawings analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploaded drawings
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Include API routers
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(quotation.router, prefix="/api/quotation", tags=["Quotation"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])

@app.get("/")
async def root():
    return {
        "message": "Manufacturing Quotation System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "manufacturing-quotation-api"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
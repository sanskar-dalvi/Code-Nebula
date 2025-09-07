"""Main API entry point.

This module initializes the FastAPI application for the C# to Neo4j pipeline.
It imports and configures all routers, middleware, and other components needed
for the API to function properly.
"""
from fastapi import FastAPI
from api.routers.process_code import router as process_router
from api.routers.trigger_etl import router as etl_router

# Create the FastAPI application with metadata
app = FastAPI(
    title="C#→Neo4j AI Pipeline",
    description="API for parsing C# code, enriching with AI, and storing in Neo4j",
    version="1.0.0"
)

# Include the routers with the /api prefix
app.include_router(process_router, prefix="/api")
app.include_router(etl_router, prefix="/api")

# Root endpoint for health check and basic information
@app.get("/")
async def root():
    """Return basic API information and health status."""
    return {
        "status": "healthy",
        "app": "C#→Neo4j AI Pipeline",
        "endpoints": [
            {"path": "/api/process", "method": "POST", "description": "Process C# files"},
            {"path": "/api/trigger-etl", "method": "POST", "description": "Trigger ETL pipeline for C# code"}
        ]
    }
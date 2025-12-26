"""
ERP Agentic Chatbot API

A robust, scalable backend for AI-powered ERP interactions.

Features:
- Swagger/OpenAPI documentation
- API Key authentication
- Multi-tenant company/project management
- LiteLLM for multi-provider LLM support
- MongoDB for data persistence
- Async operations for performance
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from contextlib import asynccontextmanager
import logging
import time

from config import settings
from services.database import db_service
from services.redis_service import redis_service
from services.erp_service import erp_service
from routes import api_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ==================== Lifespan Management ====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    logger.info("Starting up ERP Agentic Chatbot API...")
    await db_service.connect()
    
    # Connect to Redis (optional, continues if Redis is unavailable)
    try:
        await redis_service.connect()
    except Exception as e:
        logger.warning(f"Redis connection failed (continuing without Redis): {e}")
    
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await db_service.disconnect()
    await redis_service.disconnect()
    await erp_service.close()
    logger.info("Shutdown complete")


# ==================== Application Setup ====================

app = FastAPI(
    title=settings.app_name,
    description="""
## ERP Agentic Chatbot API

AI-powered chatbot that intelligently queries ERP APIs based on natural language queries.

### Features

- **Natural Language Processing**: Ask questions in plain English
- **Automatic API Selection**: AI selects the most relevant ERP APIs
- **Smart Project Detection**: Automatically determines which project you're asking about
- **Multi-tenant Support**: Supports multiple companies and projects

### Authentication

All endpoints (except health checks) require API key authentication.
Include your API key in the `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

### Getting Started

1. **Initialize Company**: Call `POST /api/init` with your company_id
   - This fetches projects, suppliers, and modules from your ERP
   
2. **Ask Questions**: Use `POST /api/chat` to query your ERP data naturally
   - Example: "Show me all outstanding supplier payments for Paradise apartments"

### How Project Selection Works

When you send a query without specifying a project:

1. The AI analyzes your query for project references
2. It matches against project names, keywords, and aliases
3. If confident (>70%), it uses the detected project
4. If unsure, it asks you to clarify which project you mean

### Example Queries

- "Show me all outstanding payments for Paradise apartments"
- "What's the total pending amount for contractors?"
- "List all overdue invoices from Alpha Structures"
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health", "description": "Health check endpoints"},
        {"name": "init", "description": "Company and project initialization"},
        {"name": "chat", "description": "Chat and query endpoints"},
        {"name": "apis", "description": "API catalog management"},
        {"name": "companies", "description": "Company management"},
    ],
)


# ==================== Middleware ====================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{round(process_time * 1000, 2)}ms"
    return response


# ==================== Routes ====================

# Include all routes from the routes module
app.include_router(api_router)


# ==================== Error Handlers ====================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": (
                exc.detail if isinstance(exc.detail, dict) else {"message": exc.detail}
            ),
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {"message": "Internal server error"},
            "status_code": 500,
        },
    )


# ==================== Entry Point ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )

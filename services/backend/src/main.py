from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .middleware.auth import verify_auth
from .routers import files, data_sources
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(files.router)
app.include_router(data_sources.router)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Middleware to handle authentication"""
    # Skip auth for health check and documentation
    if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc", "/redoc.standalone.html"]:
        logger.debug(f"Skipping auth for {request.url.path}")
        return await call_next(request)
        
    logger.debug(f"Processing request to: {request.url.path}")
    return await verify_auth(request, call_next)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.on_event("startup")
async def startup():
    """Log all registered routes on startup"""
    logger.debug("Registered routes:")
    for route in app.routes:
        logger.debug(f"  {route}")

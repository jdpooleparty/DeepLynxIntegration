from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from app.routers import ontology, data_source, ingestion, type_mapping
from app.core.auth import initialize_deep_lynx_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Deep-Lynx client on startup
    await initialize_deep_lynx_client()
    yield
    # Cleanup on shutdown if needed
    pass

app = FastAPI(
    title="Deep-Lynx Data Pipeline",
    description="API for managing data ingestion and ontology in Deep-Lynx",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API documentation"""
    return RedirectResponse(url="/docs")

# Include routers
app.include_router(ontology.router, prefix="/api/ontology", tags=["Ontology"])
app.include_router(data_source.router, prefix="/api/data-source", tags=["Data Source"])
app.include_router(ingestion.router, prefix="/api/ingestion", tags=["Data Ingestion"])
app.include_router(
    type_mapping.router,
    prefix="/api/type-mappings",
    tags=["Type Mappings"]
) 
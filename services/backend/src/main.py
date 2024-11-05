from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

app = FastAPI(
    title="Deep-Lynx Integration",
    description="API for integrating with Deep-Lynx",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic test endpoints
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint that returns a welcome message"""
    return {"message": "Welcome to Deep-Lynx Integration API"}

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
# Data Source endpoints
@app.get("/datasources", tags=["Data Sources"])
async def get_datasources():
    """Get all data sources"""
    return {"message": "List of data sources"}

@app.post("/datasources", tags=["Data Sources"])
async def create_datasource():
    """Create a new data source"""
    return {"message": "Create data source"}

@app.get("/datasources/{datasource_id}", tags=["Data Sources"])
async def get_datasource(datasource_id: str):
    """Get a specific data source by ID"""
    return {"message": f"Get data source {datasource_id}"}

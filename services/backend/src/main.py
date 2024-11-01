from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for initial testing
@app.get("/ontology")
async def get_ontology() -> Dict[str, Any]:
    return {
        "nodes": [
            {"id": 1, "name": "Person", "type": "container"},
            {"id": 2, "name": "Address", "type": "container"}
        ],
        "relationships": [
            {"source": 1, "target": 2, "type": "has"}
        ]
    }

@app.get("/datasources")
async def get_datasources() -> List[Dict[str, Any]]:
    return [
        {"id": 1, "name": "CSV Import", "type": "file", "status": "active"},
        {"id": 2, "name": "API Feed", "type": "api", "status": "inactive"}
    ]

@app.get("/typemappings")
async def get_typemappings() -> List[Dict[str, Any]]:
    return [
        {
            "id": 1,
            "sourceType": "PersonRecord",
            "targetType": "Person",
            "rules": {"name": "$.fullName", "age": "$.age"}
        }
    ]

@app.get("/")
def home():
    return "Hello, World!" 
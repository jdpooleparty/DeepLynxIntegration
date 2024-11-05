from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class OntologyClass(BaseModel):
    name: str
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict)

class RelationshipType(BaseModel):
    name: str
    description: Optional[str] = None
    source_class: str
    target_class: str
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict)

class OntologyResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]

class DataSource(BaseModel):
    name: str
    adapter_type: str
    config: Dict[str, Any]
    description: Optional[str] = None
    active: bool = True 
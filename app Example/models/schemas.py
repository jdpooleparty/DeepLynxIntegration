from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from enum import Enum
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

class DataSourceConfig(BaseModel):
    data_format: Optional[str] = None
    data_type: str = "json"
    kind: str = "standard"
    
    class Config:
        extra = "allow"  # Allow additional fields in config

class DataSource(BaseModel):
    name: str
    type: str = Field(alias="adapter_type")
    config: Dict[str, Any]
    description: Optional[str] = None
    active: bool = True

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "Sample Data Source",
                "type": "standard",
                "config": {
                    "data_type": "json",
                    "kind": "standard"
                }
            }
        }

class TransformationType(str, Enum):
    DIRECT = "direct"
    CUSTOM = "custom"
    NESTED = "nested"
    ARRAY = "array"
    REFERENCE = "reference"

class TypeTransformationRule(BaseModel):
    source_field: str
    target_field: str
    transformation_type: TransformationType
    transformation_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('transformation_config')
    def validate_config(cls, v, values):
        t_type = values.get('transformation_type')
        if t_type == TransformationType.CUSTOM and 'transform_function' not in v:
            raise ValueError("Custom transformations require 'transform_function' in config")
        if t_type == TransformationType.NESTED and 'nested_mappings' not in v:
            raise ValueError("Nested transformations require 'nested_mappings' in config")
        return v

class TypeMapping(BaseModel):
    name: str
    description: Optional[str] = None
    source_type: str
    target_type: str
    transformation_rules: List[TypeTransformationRule]
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class TypeMappingCreate(TypeMapping):
    pass

class TypeMappingUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    transformation_rules: Optional[List[TypeTransformationRule]] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class TypeMappingResponse(TypeMapping):
    id: str
    created_at: str
    updated_at: Optional[str] = None

class DataIngestionRequest(BaseModel):
    data_source_id: str
    records: List[Dict[str, Any]] 

class DataSourceResponse(BaseModel):
    id: str
    name: str
    adapter_type: str = Field(default="standard")
    active: bool = True
    archived: bool = False
    config: DataSourceConfig
    container_id: str
    created_at: datetime
    created_by: str
    modified_at: Optional[datetime] = None
    modified_by: Optional[str] = None
    data_format: Optional[str] = None
    status: str = "ready"
    status_message: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
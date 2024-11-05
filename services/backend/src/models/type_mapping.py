from pydantic import BaseModel
from typing import Optional, List

class TypeMappingBase(BaseModel):
    name: str
    source_type: str
    destination_type: str
    mapping_rules: dict

class TypeMappingCreate(TypeMappingBase):
    pass

class TypeMapping(TypeMappingBase):
    id: str
    container_id: str
    created_at: str
    updated_at: str 
from fastapi import APIRouter, HTTPException
from typing import List
from ..core.deep_lynx import get_client
from ..models.type_mapping import TypeMapping, TypeMappingCreate

router = APIRouter()

@router.get("/", response_model=List[TypeMapping])
async def get_type_mappings():
    """Get all type mappings"""
    try:
        client = get_client()
        # Get type mappings from Deep Lynx
        response = await client.type_mappings_api.list_type_mappings(
            container_id=client.container_id
        )
        return response.value
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=TypeMapping)
async def create_type_mapping(type_mapping: TypeMappingCreate):
    """Create a new type mapping"""
    try:
        client = get_client()
        # Create type mapping in Deep Lynx
        response = await client.type_mappings_api.create_type_mapping(
            container_id=client.container_id,
            type_mapping=type_mapping
        )
        return response.value
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
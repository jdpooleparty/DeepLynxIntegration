from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.core.auth import get_deep_lynx_client, DeepLynxWrapper
from app.core.type_mapping import (
    get_type_mappings,
    get_type_mapping_by_id,
    create_type_mapping,
    update_type_mapping,
    delete_type_mapping
)
from app.models.schemas import (
    TypeMapping,
    TypeMappingUpdate,
    TypeMappingResponse
)

router = APIRouter()

@router.get("/", response_model=List[TypeMappingResponse])
async def list_type_mappings(
    active_only: bool = Query(False, description="Only return active mappings"),
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> List[TypeMappingResponse]:
    """
    Retrieve all type mappings.
    """
    return await get_type_mappings(client, active_only)

@router.get("/{mapping_id}", response_model=TypeMappingResponse)
async def get_mapping(
    mapping_id: str,
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> TypeMappingResponse:
    """
    Retrieve a specific type mapping by ID.
    """
    return await get_type_mapping_by_id(client, mapping_id)

@router.post("/", response_model=TypeMappingResponse)
async def create_mapping(
    type_mapping: TypeMapping,
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> TypeMappingResponse:
    """
    Create a new type mapping.
    """
    return await create_type_mapping(client, type_mapping)

@router.put("/{mapping_id}", response_model=TypeMappingResponse)
async def update_mapping(
    mapping_id: str,
    type_mapping: TypeMappingUpdate,
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> TypeMappingResponse:
    """
    Update an existing type mapping.
    """
    return await update_type_mapping(client, mapping_id, type_mapping)

@router.delete("/{mapping_id}")
async def delete_mapping(
    mapping_id: str,
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> dict:
    """
    Delete a type mapping.
    """
    await delete_type_mapping(client, mapping_id)
    return {"message": f"Successfully deleted type mapping {mapping_id}"} 
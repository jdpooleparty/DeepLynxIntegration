from typing import List, Dict, Any, Optional
from app.core.auth import DeepLynxWrapper
from fastapi import HTTPException
from app.models.schemas import TypeMapping, TypeMappingUpdate, TypeMappingResponse
from datetime import datetime

async def get_type_mappings(
    client: DeepLynxWrapper,
    active_only: bool = False
) -> List[TypeMappingResponse]:
    """
    Retrieve all type mappings from Deep-Lynx.
    """
    try:
        response = await client.get_type_mappings(active_only=active_only)
        if not response.is_success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch type mappings: {response.error}"
            )
        return [TypeMappingResponse(**mapping) for mapping in response.data]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching type mappings: {str(e)}"
        )

async def get_type_mapping_by_id(
    client: DeepLynxWrapper,
    mapping_id: str
) -> TypeMappingResponse:
    """
    Retrieve a specific type mapping by ID.
    """
    try:
        response = await client.get_type_mapping(mapping_id)
        if not response.is_success:
            raise HTTPException(
                status_code=404,
                detail=f"Type mapping not found: {response.error}"
            )
        return TypeMappingResponse(**response.data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching type mapping: {str(e)}"
        )

async def create_type_mapping(
    client: DeepLynxWrapper,
    type_mapping: TypeMapping
) -> TypeMappingResponse:
    """
    Create a new type mapping in Deep-Lynx.
    """
    try:
        # Validate that source and target types exist
        await validate_types(client, type_mapping.source_type, type_mapping.target_type)
        
        response = await client.create_type_mapping(type_mapping.dict())
        if not response.is_success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create type mapping: {response.error}"
            )
        return TypeMappingResponse(**response.data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating type mapping: {str(e)}"
        )

async def update_type_mapping(
    client: DeepLynxWrapper,
    mapping_id: str,
    type_mapping: TypeMappingUpdate
) -> TypeMappingResponse:
    """
    Update an existing type mapping.
    """
    try:
        # Get existing mapping to ensure it exists
        existing = await get_type_mapping_by_id(client, mapping_id)
        
        update_data = type_mapping.dict(exclude_unset=True)
        response = await client.update_type_mapping(mapping_id, update_data)
        
        if not response.is_success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to update type mapping: {response.error}"
            )
        return TypeMappingResponse(**response.data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating type mapping: {str(e)}"
        )

async def delete_type_mapping(
    client: DeepLynxWrapper,
    mapping_id: str
) -> bool:
    """
    Delete a type mapping.
    """
    try:
        response = await client.delete_type_mapping(mapping_id)
        if not response.is_success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to delete type mapping: {response.error}"
            )
        return True
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting type mapping: {str(e)}"
        )

async def validate_types(
    client: DeepLynxWrapper,
    source_type: str,
    target_type: str
) -> bool:
    """
    Validate that both source and target types exist in Deep-Lynx.
    """
    try:
        # Check if types exist in Deep-Lynx
        source_response = await client.get_type(source_type)
        target_response = await client.get_type(target_type)
        
        if not source_response.is_success:
            raise HTTPException(
                status_code=400,
                detail=f"Source type '{source_type}' not found"
            )
        
        if not target_response.is_success:
            raise HTTPException(
                status_code=400,
                detail=f"Target type '{target_type}' not found"
            )
        
        return True
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating types: {str(e)}"
        ) 
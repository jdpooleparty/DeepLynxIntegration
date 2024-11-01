from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.core.auth import get_deep_lynx_client, DeepLynxWrapper
from app.core.data_source import (
    get_data_sources,
    get_data_source_by_id,
    create_data_source,
    update_data_source,
    delete_data_source
)
from app.models.schemas import DataSource, DataSourceResponse

router = APIRouter()

@router.get("/", response_model=List[DataSourceResponse])
async def list_data_sources(
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> List[DataSourceResponse]:
    """
    Retrieve all configured data sources from Deep-Lynx.
    """
    return await get_data_sources(client)

@router.get("/{source_id}", response_model=DataSourceResponse)
async def get_source(
    source_id: str,
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> DataSourceResponse:
    """
    Retrieve a specific data source by ID.
    """
    return await get_data_source_by_id(client, source_id)

@router.post("/", response_model=DataSourceResponse)
async def add_data_source(
    data_source: DataSource,
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> DataSourceResponse:
    """
    Create a new data source configuration in Deep-Lynx.
    """
    return await create_data_source(client, data_source)

@router.put("/{source_id}", response_model=DataSourceResponse)
async def update_source(
    source_id: str,
    data_source: DataSource,
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> DataSourceResponse:
    """
    Update an existing data source configuration.
    """
    return await update_data_source(client, source_id, data_source)

@router.delete("/{source_id}")
async def delete_source(
    source_id: str,
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> Dict[str, str]:
    """
    Delete a data source configuration.
    """
    await delete_data_source(client, source_id)
    return {"message": f"Successfully deleted data source {source_id}"} 
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..core.deep_lynx import get_client
from ..models.data_source import DataSource, DataSourceCreate, DataSourceConfig
from ..auth.jwthandler import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[DataSource], dependencies=[Depends(get_current_user)])
async def get_data_sources():
    """Get all data sources"""
    try:
        client = get_client()
        logger.debug(f"Fetching data sources for container {client.container_id}")
        
        response = client.datasources_api.list_data_sources(
            container_id=client.container_id
        )
        
        if not response or not hasattr(response, 'value'):
            return []
            
        return [
            DataSource(
                id=str(source.id),
                name=source.name,
                adapter_type=source.adapter_type,
                config=DataSourceConfig(
                    type=source.config.get('type', ''),
                    description=source.config.get('description'),
                    data_format=source.config.get('data_format')
                ) if isinstance(source.config, dict) else DataSourceConfig(type=''),
                container_id=str(source.container_id),
                active=source.active,
                created_at=source.created_at,
                updated_at=source.modified_at or source.created_at
            ) for source in response.value
        ]
        
    except Exception as e:
        logger.error(f"Error fetching data sources: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch data sources: {str(e)}"
        )

@router.post("/", response_model=DataSource, dependencies=[Depends(get_current_user)])
async def create_data_source(data_source: DataSourceCreate):
    """Create a new data source"""
    try:
        client = get_client()
        logger.debug(f"Creating data source: {data_source.name}")
        
        # Convert to Deep Lynx format
        source_data = {
            "name": data_source.name,
            "adapter_type": data_source.adapter_type,
            "config": {
                "type": data_source.config.type,
                "description": data_source.config.description,
                "data_format": data_source.config.data_format
            }
        }
        
        response = client.datasources_api.create_data_source(
            container_id=client.container_id,
            body=source_data
        )
        
        if not response or not hasattr(response, 'value'):
            raise HTTPException(
                status_code=500,
                detail="Failed to create data source: Invalid response"
            )
            
        source = response.value
        return DataSource(
            id=str(source.id),
            name=source.name,
            adapter_type=source.adapter_type,
            config=DataSourceConfig(
                type=source.config.get('type', data_source.config.type),
                description=source.config.get('description', data_source.config.description),
                data_format=source.config.get('data_format', data_source.config.data_format)
            ),
            container_id=str(source.container_id),
            active=source.active,
            created_at=source.created_at,
            updated_at=source.modified_at or source.created_at
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating data source: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create data source: {str(e)}"
        )

@router.get("/{source_id}", response_model=DataSource, dependencies=[Depends(get_current_user)])
async def get_data_source(source_id: str):
    """Get a specific data source"""
    try:
        client = get_client()
        logger.debug(f"Fetching data source {source_id}")
        
        # Use list_data_sources and filter since get_data_source doesn't exist
        response = client.datasources_api.list_data_sources(
            container_id=client.container_id
        )
        
        if not response or not hasattr(response, 'value'):
            raise HTTPException(status_code=404, detail=f"Data source {source_id} not found")
            
        for source in response.value:
            if str(source.id) == source_id:
                return DataSource(
                    id=str(source.id),
                    name=source.name,
                    adapter_type=source.adapter_type,
                    config=DataSourceConfig(
                        type=source.config.get('type', ''),
                        description=source.config.get('description'),
                        data_format=source.config.get('data_format')
                    ) if isinstance(source.config, dict) else DataSourceConfig(type=''),
                    container_id=str(source.container_id),
                    active=source.active,
                    created_at=source.created_at,
                    updated_at=source.modified_at or source.created_at
                )
                
        raise HTTPException(status_code=404, detail=f"Data source {source_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching data source {source_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch data source: {str(e)}"
        )
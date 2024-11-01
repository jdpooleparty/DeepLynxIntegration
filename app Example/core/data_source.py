from typing import List, Dict, Any
from app.core.auth import DeepLynxWrapper
from fastapi import HTTPException
from app.models.schemas import DataSource
import logging

logger = logging.getLogger(__name__)

async def get_data_sources(client: DeepLynxWrapper) -> List[Dict[str, Any]]:
    """Get all data sources"""
    try:
        container_id = client.api_client.configuration.container_id
        # Add debug logging
        logger.debug(f"Using container_id: {container_id}")
        
        response = client.datasources_api.list_data_sources(
            container_id=str(container_id)
        )
        
        # Add debug logging for raw response
        logger.debug(f"Raw Deep Lynx response: {response}")
        
        if not response:
            logger.warning("No response received from Deep Lynx")
            return []
            
        # Deep Lynx returns response.value for successful calls
        if hasattr(response, 'value'):
            # Sometimes value is a list, sometimes it's a dict containing the list
            if isinstance(response.value, list):
                return response.value
            elif isinstance(response.value, dict) and 'data_sources' in response.value:
                return response.value['data_sources']
            elif isinstance(response.value, dict):
                return [response.value]
            else:
                logger.warning(f"Unexpected value type in response: {type(response.value)}")
                return []
        else:
            logger.warning(f"Response has no 'value' attribute: {response}")
            return []
        
    except Exception as e:
        logger.error(f"Error fetching data sources: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching data sources: {str(e)}"
        )

async def get_data_source_by_id(
    client: DeepLynxWrapper,
    source_id: str
) -> Dict[str, Any]:
    """Get a specific data source by ID"""
    try:
        container_id = client.api_client.configuration.container_id
        response = client.datasources_api.get_data_source(
            container_id=container_id,
            data_source_id=source_id
        )
        
        if not response:
            raise HTTPException(
                status_code=404,
                detail=f"Data source {source_id} not found"
            )
            
        # Extract the first value if it's wrapped
        if hasattr(response, 'value'):
            return response.value[0] if isinstance(response.value, list) else response.value
        elif isinstance(response, dict) and 'value' in response:
            return response['value'][0] if isinstance(response['value'], list) else response['value']
        else:
            return response
        
    except Exception as e:
        logger.error(f"Error fetching data source {source_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching data source: {str(e)}"
        )

async def create_data_source(
    client: DeepLynxWrapper,
    data_source: DataSource
) -> Dict[str, Any]:
    try:
        response = await client.create_data_source(
            name=data_source.name,
            type=data_source.type,
            config=data_source.config,
            description=data_source.description
        )
        if not response.is_success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create data source: {response.error}"
            )
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating data source: {str(e)}"
        )

async def update_data_source(
    client: DeepLynxWrapper,
    source_id: str,
    data_source: DataSource
) -> Dict[str, Any]:
    try:
        response = await client.update_data_source(
            source_id=source_id,
            name=data_source.name,
            type=data_source.type,
            config=data_source.config,
            description=data_source.description
        )
        if not response.is_success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to update data source: {response.error}"
            )
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating data source: {str(e)}"
        )

async def delete_data_source(
    client: DeepLynxWrapper,
    source_id: str
) -> bool:
    try:
        response = await client.delete_data_source(source_id)
        if not response.is_success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to delete data source: {response.error}"
            )
        return True
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting data source: {str(e)}"
        ) 
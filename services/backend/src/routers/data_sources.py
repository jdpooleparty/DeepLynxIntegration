from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging
from ..core.deep_lynx import DeepLynxClient, get_client
from deep_lynx.models import (
    DataSource,
    CreateDataSourceRequest,
    DataSourceConfig
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasources", tags=["data_sources"])

@router.post("", status_code=201)
async def create_data_source(
    data_source: Dict[str, Any],
    client: DeepLynxClient = Depends(get_client)
) -> Dict[str, Any]:
    """Create a new data source"""
    try:
        logger.debug(f"Creating data source with config: {data_source}")
        
        # Create config dictionary matching SDK expectations
        config_dict = {
            "data_source": {
                "adapter_type": data_source.get("adapter_type"),
                "type": data_source.get("type"),
                "config": data_source.get("config", {}),
            }
        }
        
        # Add name to the config if provided
        if "name" in data_source:
            config_dict["data_source"]["name"] = data_source["name"]
            
        logger.debug(f"Transformed config for SDK: {config_dict}")
        
        # Create request using SDK model
        request = CreateDataSourceRequest(**config_dict)
        
        # Make API call
        response = await client.create_data_source(request)
        logger.info(f"Successfully created data source: {response.value.id}")
        
        return {
            "id": response.value.id,
            "name": response.value.name,
            "type": response.value.type,
            "adapter_type": response.value.adapter_type,
            "config": response.value.config
        }
        
    except KeyError as e:
        logger.error(f"Missing required field: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Missing required field: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to create data source: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def list_data_sources(
    client: DeepLynxClient = Depends(get_client)
) -> Dict[str, Any]:
    """List all data sources"""
    try:
        logger.debug("Listing data sources")
        response = await client.list_data_sources()
        return {
            "data_sources": [
                {
                    "id": ds.id,
                    "name": ds.name,
                    "type": ds.type,
                    "adapter_type": ds.adapter_type,
                    "config": ds.config
                }
                for ds in response.value
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list data sources: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

from typing import List, Dict, Any, Optional
from app.core.auth import DeepLynxWrapper
from fastapi import HTTPException
from app.models.schemas import OntologyClass, RelationshipType
import logging

logger = logging.getLogger(__name__)

async def get_ontology_classes(client: DeepLynxWrapper) -> List[Dict[str, Any]]:
    try:
        container_id = client.api_client.configuration.container_id
        
        response = client.metatypes_api.list_metatypes(
            container_id=container_id
        )
        
        if not response:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch ontology classes: No response"
            )
            
        # Limit the response to 2 classes
        if isinstance(response, list):
            return response[:2]  # Return first 2 classes
        elif hasattr(response, 'value') and isinstance(response.value, list):
            return response.value[:2]  # Return first 2 classes from response.value
        else:
            logger.warning(f"Unexpected response format: {type(response)}")
            return []
        
    except Exception as e:
        logger.error(f"Error fetching ontology classes: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching ontology classes: {str(e)}"
        )

async def create_ontology_class(
    client: DeepLynxWrapper,
    ontology_class: OntologyClass
) -> Dict[str, Any]:
    try:
        container_id = client.api_client.configuration.container_id
        
        response = client.metatypes_api.create_metatype(
            container_id=container_id,
            body={
                "name": ontology_class.name,
                "description": ontology_class.description,
                "properties": ontology_class.properties
            }
        )
        
        if not response:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create ontology class: No response"
            )
            
        return response
        
    except Exception as e:
        logger.error(f"Error creating ontology class: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating ontology class: {str(e)}"
        )

async def create_relationship_type(
    client: DeepLynxWrapper,
    relationship: RelationshipType
) -> Dict[str, Any]:
    try:
        container_id = client.api_client.configuration.container_id
        
        response = await client.relationships_api.create_container_metatype_relationship(
            container_id=container_id,
            name=relationship.name,
            description=relationship.description,
            source_metatype_id=relationship.source_class,
            destination_metatype_id=relationship.target_class
        )
        
        if not response or not hasattr(response, 'value'):
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create relationship type: Invalid response"
            )
            
        return response.value
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating relationship type: {str(e)}"
        )

async def update_ontology_class(
    client: DeepLynxWrapper,
    class_id: str,
    ontology_class: OntologyClass
) -> Dict[str, Any]:
    try:
        container_id = client.api_client.configuration.container_id
        
        response = await client.metatypes_api.update_container_metatype(
            container_id=container_id,
            metatype_id=class_id,
            name=ontology_class.name,
            description=ontology_class.description,
            properties=ontology_class.properties
        )
        
        if not response or not hasattr(response, 'value'):
            raise HTTPException(
                status_code=400,
                detail=f"Failed to update ontology class: Invalid response"
            )
            
        return response.value
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating ontology class: {str(e)}"
        )

async def delete_ontology_class(
    client: DeepLynxWrapper,
    class_id: str
) -> bool:
    try:
        container_id = client.api_client.configuration.container_id
        
        response = await client.metatypes_api.delete_container_metatype(
            container_id=container_id,
            metatype_id=class_id
        )
        
        if not response or not hasattr(response, 'value'):
            raise HTTPException(
                status_code=400,
                detail=f"Failed to delete ontology class: Invalid response"
            )
            
        return True
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting ontology class: {str(e)}"
        ) 
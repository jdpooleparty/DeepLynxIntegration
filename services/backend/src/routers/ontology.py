from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..core.deep_lynx import get_client
from ..models.schemas import OntologyClass, RelationshipType, OntologyResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=OntologyResponse)
async def get_ontology():
    """Get full ontology with classes and relationships"""
    try:
        client = get_client()
        
        # Get metatypes (classes)
        metatypes_response = client.metatypes_api.list_metatypes(
            container_id=client.container_id
        )
        nodes = []
        if metatypes_response and hasattr(metatypes_response, 'value'):
            nodes = [
                {
                    "id": str(mt.id),
                    "name": mt.name,
                    "type": "metatype",
                    "description": mt.description,
                    "properties": mt.properties if hasattr(mt, 'properties') else {},
                    "created_at": str(mt.created_at) if hasattr(mt, 'created_at') else None
                } for mt in metatypes_response.value
            ]

        # Get relationships
        relationships_response = client.relationships_api.list_metatype_relationships(
            container_id=client.container_id
        )
        relationships = []
        if relationships_response and hasattr(relationships_response, 'value'):
            relationships = [
                {
                    "id": str(rel.id),
                    "name": rel.name,
                    "description": rel.description if hasattr(rel, 'description') else None,
                    "source": str(rel.source_metatype_id),
                    "target": str(rel.destination_metatype_id),
                    "properties": rel.properties if hasattr(rel, 'properties') else {}
                } for rel in relationships_response.value
            ]

        return OntologyResponse(nodes=nodes, relationships=relationships)

    except Exception as e:
        logger.error(f"Error fetching ontology: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/classes", response_model=Dict[str, Any])
async def create_class(class_data: OntologyClass):
    """Create a new ontology class"""
    try:
        client = get_client()
        response = client.metatypes_api.create_metatype(
            container_id=client.config.container_id,
            body={
                "name": class_data.name,
                "description": class_data.description,
                "properties": class_data.properties
            }
        )
        if response and hasattr(response, 'value'):
            return response.value
        raise HTTPException(status_code=400, detail="Failed to create class")
    except Exception as e:
        logger.error(f"Error creating class: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/relationships", response_model=Dict[str, Any])
async def create_relationship(relationship: RelationshipType):
    """Create a new relationship between classes"""
    try:
        client = get_client()
        response = client.relationships_api.create_metatype_relationship(
            container_id=client.config.container_id,
            body={
                "name": relationship.name,
                "description": relationship.description,
                "source_metatype_id": relationship.source_class,
                "destination_metatype_id": relationship.target_class,
                "properties": relationship.properties
            }
        )
        if response and hasattr(response, 'value'):
            return response.value
        raise HTTPException(status_code=400, detail="Failed to create relationship")
    except Exception as e:
        logger.error(f"Error creating relationship: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
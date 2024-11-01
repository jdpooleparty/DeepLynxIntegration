from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.core.auth import get_deep_lynx_client, DeepLynxWrapper
from app.core.ontology import (
    get_ontology_classes,
    create_ontology_class,
    create_relationship_type,
    update_ontology_class,
    delete_ontology_class
)
from app.models.schemas import OntologyClass, RelationshipType

router = APIRouter()

@router.get("/classes", response_model=List[Dict[str, Any]])
async def list_ontology_classes(
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> List[Dict[str, Any]]:
    """
    Retrieve all ontology classes from Deep-Lynx.
    """
    return await get_ontology_classes(client)

@router.post("/classes", response_model=Dict[str, Any])
async def add_ontology_class(
    ontology_class: OntologyClass,
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> Dict[str, Any]:
    """
    Create a new ontology class in Deep-Lynx.
    """
    return await create_ontology_class(client, ontology_class)

@router.post("/relationships", response_model=Dict[str, Any])
async def add_relationship_type(
    relationship: RelationshipType,
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> Dict[str, Any]:
    """
    Create a new relationship type between ontology classes.
    """
    return await create_relationship_type(client, relationship)

@router.put("/classes/{class_id}", response_model=Dict[str, Any])
async def update_class(
    class_id: str,
    ontology_class: OntologyClass,
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> Dict[str, Any]:
    """
    Update an existing ontology class.
    """
    return await update_ontology_class(client, class_id, ontology_class)

@router.delete("/classes/{class_id}")
async def delete_class(
    class_id: str,
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> Dict[str, str]:
    """
    Delete an ontology class.
    """
    await delete_ontology_class(client, class_id)
    return {"message": f"Successfully deleted class {class_id}"} 
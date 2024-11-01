from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.core.auth import get_deep_lynx_client, DeepLynxWrapper
from app.core.ingestion import check_ingestion_status
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/status/{batch_id}")
async def get_ingestion_status(
    batch_id: str,
    client: DeepLynxWrapper = Depends(get_deep_lynx_client)
) -> Dict[str, Any]:
    """
    Check the status of a data ingestion batch.
    """
    try:
        logger.debug(f"Checking status for batch ID: {batch_id}")
        status = await check_ingestion_status(client, batch_id)
        return {
            "batch_id": batch_id,
            "status": status.get("status", "unknown"),
            "records_processed": status.get("records_processed", 0),
            "errors": status.get("errors", []),
            "completed_at": status.get("completed_at")
        }
    except Exception as e:
        logger.error(f"Error checking ingestion status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check ingestion status: {str(e)}"
        ) 
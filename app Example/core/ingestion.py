from typing import List, Dict, Any, Optional
from app.core.auth import DeepLynxWrapper
from fastapi import HTTPException
from app.models.schemas import DataIngestionRequest
import asyncio
from datetime import datetime
from app.core.transform_pipeline import process_data_transformation
from app.core.type_mapping import get_type_mapping_by_id
import logging

logger = logging.getLogger(__name__)

async def validate_data_format(records: List[Dict[str, Any]]) -> bool:
    """
    Validate the format of incoming data records.
    Returns True if valid, raises HTTPException if invalid.
    """
    if not records:
        raise HTTPException(
            status_code=400,
            detail="No records provided for ingestion"
        )
    
    try:
        # Add custom validation logic here based on your data requirements
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("Each record must be a dictionary")
            
        return True
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data format: {str(e)}"
        )

async def ingest_data_batch(
    client: DeepLynxWrapper,
    data_source_id: str,
    records: List[Dict[str, Any]],
    type_mapping_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ingest a batch of records into Deep-Lynx with optional transformation.
    """
    try:
        # Validate data format
        await validate_data_format(records)
        
        # Transform data if type mapping is provided
        if type_mapping_id:
            type_mapping = await get_type_mapping_by_id(client, type_mapping_id)
            records = await process_data_transformation(client, records, type_mapping)
        
        # Add metadata to the batch
        batch_metadata = {
            "ingestion_time": datetime.utcnow().isoformat(),
            "record_count": len(records),
            "type_mapping_id": type_mapping_id
        }
        
        response = await client.ingest_data(
            data_source_id=data_source_id,
            data=records,
            metadata=batch_metadata
        )
        
        if not response.is_success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to ingest data: {response.error}"
            )
        
        return {
            "success": True,
            "records_processed": len(records),
            "batch_id": response.data.get("batch_id"),
            "metadata": batch_metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during data ingestion: {str(e)}"
        )

async def get_ingestion_status(
    client: DeepLynxWrapper,
    batch_id: str
) -> Dict[str, Any]:
    """
    Get the status of a specific ingestion batch.
    """
    try:
        response = await client.get_ingestion_status(batch_id)
        if not response.is_success:
            raise HTTPException(
                status_code=404,
                detail=f"Batch not found: {response.error}"
            )
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching ingestion status: {str(e)}"
        )

async def ingest_data_stream(
    client: DeepLynxWrapper,
    data_source_id: str,
    records: List[Dict[str, Any]],
    batch_size: int = 1000
) -> Dict[str, Any]:
    """
    Stream large datasets in smaller batches for better performance.
    """
    try:
        total_records = len(records)
        processed_records = 0
        batch_results = []

        # Process records in batches
        for i in range(0, total_records, batch_size):
            batch = records[i:i + batch_size]
            result = await ingest_data_batch(client, data_source_id, batch)
            processed_records += len(batch)
            batch_results.append(result)

            # Add a small delay between batches to prevent overwhelming the server
            await asyncio.sleep(0.1)

        return {
            "success": True,
            "total_records_processed": processed_records,
            "batch_count": len(batch_results),
            "batch_results": batch_results
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during stream ingestion: {str(e)}"
        )

async def check_ingestion_status(
    client: DeepLynxWrapper,
    batch_id: str
) -> Dict[str, Any]:
    """Check the status of an ingestion batch"""
    try:
        # The correct method is get_queue_status
        response = client.datasources_api.get_queue_status(
            container_id=str(client.api_client.configuration.container_id),
            data_source_id=batch_id
        )
        
        logger.debug(f"Raw status response: {response}")
        
        if not response:
            raise HTTPException(
                status_code=404,
                detail=f"No status found for batch {batch_id}"
            )
            
        if hasattr(response, 'value'):
            # Handle array of queue items
            queue_items = response.value if isinstance(response.value, list) else [response.value]
            # Find the relevant queue item for this batch
            for item in queue_items:
                if str(item.get('id')) == batch_id:
                    return {
                        "status": item.get("status", "unknown"),
                        "records_processed": item.get("records_processed", 0),
                        "errors": item.get("errors", []),
                        "completed_at": item.get("completed_at")
                    }
            # If we didn't find the batch, return not found
            raise HTTPException(
                status_code=404,
                detail=f"No status found for batch {batch_id}"
            )
        else:
            logger.warning(f"Unexpected response format: {type(response)}")
            return {
                "status": "unknown",
                "error": "Unexpected response format from Deep Lynx"
            }
            
    except Exception as e:
        logger.error(f"Error checking ingestion status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check ingestion status: {str(e)}"
        ) 
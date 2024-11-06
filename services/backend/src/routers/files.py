from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from typing import Optional, Dict, Any
from ..core.deep_lynx import DeepLynxClient, get_client
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    node_id: Optional[str] = Form(None),
    metadata: Optional[Dict[str, Any]] = Form(None),
    client: DeepLynxClient = Depends(get_client)
):
    """
    Upload a file to Deep Lynx and optionally associate it with a node
    """
    logger.debug(f"Starting file upload for {file.filename}")
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            logger.debug(f"Created temporary file at {temp_file_path}")

        try:
            # Upload file
            logger.debug("Preparing file upload with metadata")
            file_response = await client.upload_file(
                temp_file_path,
                metadata={
                    "filename": file.filename,
                    "content_type": file.content_type,
                    **(metadata or {})
                }
            )
            logger.debug(f"File upload response received: {file_response}")

            # If node_id is provided, associate file with node
            if node_id and file_response.get("id"):
                logger.debug(f"Associating file {file_response['id']} with node {node_id}")
                association_response = await client.associate_file_with_node(
                    file_response["id"],
                    node_id
                )
                return {
                    "message": "File uploaded and associated with node",
                    "file": file_response,
                    "association": association_response
                }

            return {
                "message": "File uploaded successfully",
                "file": file_response
            }

        finally:
            # Clean up temporary file
            logger.debug(f"Cleaning up temporary file {temp_file_path}")
            os.unlink(temp_file_path)

    except Exception as e:
        logger.error(f"Failed to handle file upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to handle file upload: {str(e)}"
        )

@router.get("/nodes/{node_id}/files")
async def get_node_files(
    node_id: str,
    client: DeepLynxClient = Depends(get_client)
):
    """
    Get all files associated with a specific node
    """
    logger.debug(f"Getting files for node {node_id}")
    try:
        files = await client.get_node_files(node_id)
        logger.debug(f"Retrieved files: {files}")
        return {
            "message": "Files retrieved successfully",
            "files": files
        }
    except Exception as e:
        logger.error(f"Failed to retrieve node files: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve node files: {str(e)}"
        ) 
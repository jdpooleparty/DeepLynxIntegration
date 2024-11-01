from typing import List, Dict, Any
from fastapi import HTTPException
from app.core.transformation import apply_transformation_mapping, TransformationError
from app.models.schemas import TypeMapping
from app.core.auth import DeepLynxWrapper

async def process_data_transformation(
    client: DeepLynxWrapper,
    data: List[Dict[str, Any]],
    type_mapping: TypeMapping
) -> List[Dict[str, Any]]:
    """
    Process a list of data records through the transformation pipeline.
    """
    transformed_data = []
    errors = []

    for index, record in enumerate(data):
        try:
            transformed_record = await apply_transformation_mapping(
                record,
                type_mapping
            )
            transformed_data.append(transformed_record)
        except TransformationError as e:
            errors.append({
                'record_index': index,
                'error': str(e),
                'record': record
            })

    if errors:
        # Log errors but continue processing
        await log_transformation_errors(client, errors)
        
    return transformed_data

async def log_transformation_errors(
    client: DeepLynxWrapper,
    errors: List[Dict[str, Any]]
) -> None:
    """
    Log transformation errors to Deep-Lynx for monitoring and debugging.
    """
    try:
        await client.log_errors(
            error_type="transformation_error",
            errors=errors
        )
    except Exception as e:
        # Don't fail the transformation if logging fails
        print(f"Failed to log transformation errors: {str(e)}")

async def validate_transformed_data(
    transformed_data: List[Dict[str, Any]],
    target_type: str
) -> bool:
    """
    Validate transformed data against target type schema.
    """
    # Implementation would depend on Deep-Lynx's schema validation capabilities
    # This is a placeholder for the actual implementation
    return True 
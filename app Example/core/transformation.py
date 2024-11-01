from typing import Any, Dict, List, Optional, Union
from fastapi import HTTPException
from app.models.schemas import TransformationType, TypeTransformationRule, TypeMapping
import json
from datetime import datetime

class TransformationError(Exception):
    """Custom exception for transformation errors"""
    pass

async def transform_value(
    value: Any,
    rule: TypeTransformationRule
) -> Any:
    """
    Transform a single value based on the transformation rule.
    """
    try:
        if rule.transformation_type == TransformationType.DIRECT:
            return value
        
        elif rule.transformation_type == TransformationType.CUSTOM:
            transform_func = rule.transformation_config.get('transform_function')
            if not transform_func:
                raise TransformationError("Missing transform_function in config")
            # Execute custom transformation function
            return await execute_custom_transform(value, transform_func)
        
        elif rule.transformation_type == TransformationType.NESTED:
            if not isinstance(value, dict):
                raise TransformationError("Value must be a dictionary for nested transformation")
            nested_mappings = rule.transformation_config.get('nested_mappings', [])
            return await transform_nested_object(value, nested_mappings)
        
        elif rule.transformation_type == TransformationType.ARRAY:
            if not isinstance(value, (list, tuple)):
                raise TransformationError("Value must be an array for array transformation")
            array_config = rule.transformation_config.get('array_config', {})
            return await transform_array(value, array_config)
        
        elif rule.transformation_type == TransformationType.REFERENCE:
            ref_config = rule.transformation_config.get('reference_config', {})
            return await resolve_reference(value, ref_config)
        
        else:
            raise TransformationError(f"Unsupported transformation type: {rule.transformation_type}")
            
    except Exception as e:
        raise TransformationError(f"Transformation failed: {str(e)}")

async def execute_custom_transform(
    value: Any,
    transform_func: str
) -> Any:
    """
    Execute a custom transformation function.
    The function should be a string containing Python code.
    """
    try:
        # Create a safe context for execution
        context = {
            'value': value,
            'datetime': datetime,
            'json': json
        }
        
        # Execute the transformation function
        exec(transform_func, context)
        if 'result' not in context:
            raise TransformationError("Custom transform function must set 'result' variable")
        
        return context['result']
    except Exception as e:
        raise TransformationError(f"Custom transformation failed: {str(e)}")

async def transform_nested_object(
    value: Dict[str, Any],
    nested_mappings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Transform a nested object using provided mappings.
    """
    result = {}
    for mapping in nested_mappings:
        source_field = mapping.get('source_field')
        target_field = mapping.get('target_field')
        transform_rule = TypeTransformationRule(**mapping.get('rule', {}))
        
        if source_field in value:
            try:
                transformed_value = await transform_value(
                    value[source_field],
                    transform_rule
                )
                result[target_field] = transformed_value
            except Exception as e:
                raise TransformationError(
                    f"Nested transformation failed for field {source_field}: {str(e)}"
                )
    
    return result

async def transform_array(
    value: List[Any],
    array_config: Dict[str, Any]
) -> List[Any]:
    """
    Transform an array of values using provided configuration.
    """
    try:
        transform_rule = TypeTransformationRule(**array_config.get('item_transform', {}))
        result = []
        
        for item in value:
            transformed_item = await transform_value(item, transform_rule)
            result.append(transformed_item)
        
        return result
    except Exception as e:
        raise TransformationError(f"Array transformation failed: {str(e)}")

async def resolve_reference(
    value: Any,
    ref_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Resolve a reference to another entity in Deep-Lynx.
    """
    try:
        ref_type = ref_config.get('ref_type')
        ref_field = ref_config.get('ref_field', 'id')
        
        if not ref_type:
            raise TransformationError("Reference type not specified")
        
        # Here you would typically query Deep-Lynx to resolve the reference
        # This is a placeholder for the actual implementation
        reference = {
            'type': ref_type,
            'id': value,
            'ref_field': ref_field
        }
        
        return reference
    except Exception as e:
        raise TransformationError(f"Reference resolution failed: {str(e)}")

async def apply_transformation_mapping(
    data: Dict[str, Any],
    type_mapping: TypeMapping
) -> Dict[str, Any]:
    """
    Apply a complete type mapping to transform data from source to target type.
    """
    try:
        result = {
            '_type': type_mapping.target_type,
            '_metadata': {
                'source_type': type_mapping.source_type,
                'mapping_name': type_mapping.name,
                'transformed_at': datetime.utcnow().isoformat()
            }
        }
        
        for rule in type_mapping.transformation_rules:
            if rule.source_field in data:
                try:
                    transformed_value = await transform_value(
                        data[rule.source_field],
                        rule
                    )
                    result[rule.target_field] = transformed_value
                except TransformationError as e:
                    raise TransformationError(
                        f"Transformation failed for field {rule.source_field}: {str(e)}"
                    )
        
        return result
    except Exception as e:
        raise TransformationError(
            f"Failed to apply transformation mapping: {str(e)}"
        ) 
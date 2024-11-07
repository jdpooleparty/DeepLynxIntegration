from typing import Dict, List, Any, Optional
from deep_lynx import (
    Configuration, 
    ApiClient,
    DataSourcesApi,
    DataTypeMappingsApi,
    MetatypesApi,
    ContainersApi
)
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class DeepLynxManager:
    """Manager class for Deep Lynx operations with enhanced error handling and logging"""
    
    def __init__(self, config: Configuration, container_id: str):
        """Initialize Deep Lynx manager with configuration"""
        self.api_client = ApiClient(config)
        self.container_id = container_id
        
        # Initialize API interfaces
        self.datasources_api = DataSourcesApi(self.api_client)
        self.mappings_api = DataTypeMappingsApi(self.api_client)
        self.metatypes_api = MetatypesApi(self.api_client)
        self.containers_api = ContainersApi(self.api_client)
        
        # Debug logging
        logger.debug(f"Initialized Deep Lynx Manager for container: {container_id}")

    async def create_data_source(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new data source with enhanced error handling"""
        try:
            # Prepare data source configuration
            source_config = {
                "name": name,
                "adapter_type": "standard",  # Default adapter type
                "active": True,
                "config": {
                    "type": config.get("type", "manual"),
                    "data_format": config.get("data_format", "json"),
                    "options": config.get("options", {})
                }
            }

            # Debug logging
            logger.debug(f"Creating data source with config: {json.dumps(source_config, indent=2)}")

            # Create data source
            response = self.datasources_api.create_data_source(
                container_id=self.container_id,
                body=source_config
            )

            logger.info(f"Successfully created data source: {name} (ID: {response.value.id})")
            return response.value

        except Exception as e:
            logger.error(f"Failed to create data source: {str(e)}")
            raise

    async def create_data_mapping(
        self,
        source_id: str,
        metatype_id: str,
        mapping_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a data mapping between source and metatype"""
        try:
            # Prepare mapping configuration
            mapping = {
                "data_source_id": source_id,
                "container_id": self.container_id,
                "metatype_id": metatype_id,
                "transformations": mapping_config.get("transformations", []),
                "active": True
            }

            logger.debug(f"Creating mapping with config: {json.dumps(mapping, indent=2)}")

            response = self.mappings_api.create_data_type_mapping(
                container_id=self.container_id,
                data_source_id=source_id,
                body=mapping
            )

            logger.info(f"Successfully created mapping for source {source_id} to metatype {metatype_id}")
            return response.value

        except Exception as e:
            logger.error(f"Failed to create mapping: {str(e)}")
            raise

    async def import_data(
        self,
        source_id: str,
        data: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """Import data in batches with progress tracking"""
        try:
            total_records = len(data)
            processed = 0
            results = []

            # Process data in batches
            for i in range(0, total_records, batch_size):
                batch = data[i:i + batch_size]
                
                # Create import
                import_result = self.datasources_api.create_manual_import(
                    container_id=self.container_id,
                    data_source_id=source_id,
                    body=batch
                )

                processed += len(batch)
                results.append(import_result.value)

                # Log progress
                progress = (processed / total_records) * 100
                logger.info(f"Import progress: {progress:.2f}% ({processed}/{total_records})")

            return {
                "total_processed": processed,
                "import_results": results,
                "success": True
            }

        except Exception as e:
            logger.error(f"Failed to import data: {str(e)}")
            raise

    async def validate_mapping(
        self,
        source_id: str,
        mapping_id: str,
        sample_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate mapping configuration with sample data"""
        try:
            # Get mapping configuration
            mapping = self.mappings_api.retrieve_data_type_mapping(
                container_id=self.container_id,
                data_source_id=source_id,
                mapping_id=mapping_id
            )

            # Validate sample data against mapping
            validation_results = []
            for record in sample_data:
                try:
                    # Apply transformations
                    transformed_data = self._apply_transformations(
                        record,
                        mapping.value.transformations
                    )
                    validation_results.append({
                        "original": record,
                        "transformed": transformed_data,
                        "valid": True
                    })
                except Exception as e:
                    validation_results.append({
                        "original": record,
                        "error": str(e),
                        "valid": False
                    })

            return {
                "mapping_id": mapping_id,
                "validation_results": validation_results,
                "success_rate": sum(1 for r in validation_results if r["valid"]) / len(validation_results)
            }

        except Exception as e:
            logger.error(f"Mapping validation failed: {str(e)}")
            raise

    def _apply_transformations(self, data: Dict[str, Any], transformations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply transformation rules to data"""
        transformed = {}
        for transform in transformations:
            source_field = transform.get("source_field")
            target_field = transform.get("target_field")
            transform_type = transform.get("type")

            if source_field and target_field:
                value = data.get(source_field)
                
                # Apply transformation based on type
                if transform_type == "date":
                    value = self._transform_date(value)
                elif transform_type == "number":
                    value = self._transform_number(value)
                elif transform_type == "string":
                    value = str(value) if value is not None else None

                transformed[target_field] = value

        return transformed

    @staticmethod
    def _transform_date(value: Any) -> Optional[str]:
        """Transform date values to ISO format"""
        if not value:
            return None
        try:
            if isinstance(value, str):
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            elif isinstance(value, (int, float)):
                dt = datetime.fromtimestamp(value)
            else:
                return None
            return dt.isoformat()
        except Exception:
            return None

    @staticmethod
    def _transform_number(value: Any) -> Optional[float]:
        """Transform numeric values"""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None 
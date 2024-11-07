from deep_lynx import Configuration
from core.deep_lynx_manager import DeepLynxManager

async def main():
    # Initialize configuration
    config = Configuration()
    config.host = "http://localhost:8090"
    
    # Create manager instance
    manager = DeepLynxManager(config, container_id="your_container_id")
    
    # Create data source
    source = await manager.create_data_source(
        name="test_source",
        config={
            "type": "manual",
            "data_format": "json",
            "options": {
                "validation": True
            }
        }
    )
    
    # Create mapping
    mapping = await manager.create_data_mapping(
        source_id=source.id,
        metatype_id="your_metatype_id",
        mapping_config={
            "transformations": [
                {
                    "source_field": "timestamp",
                    "target_field": "created_at",
                    "type": "date"
                },
                {
                    "source_field": "value",
                    "target_field": "measurement",
                    "type": "number"
                }
            ]
        }
    )
    
    # Import data
    sample_data = [
        {"timestamp": "2024-01-01T00:00:00Z", "value": "123.45"},
        {"timestamp": "2024-01-01T00:01:00Z", "value": "456.78"}
    ]
    
    import_result = await manager.import_data(
        source_id=source.id,
        data=sample_data
    )
    
    # Validate mapping
    validation = await manager.validate_mapping(
        source_id=source.id,
        mapping_id=mapping.id,
        sample_data=sample_data
    ) 
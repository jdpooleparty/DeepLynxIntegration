from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional
from datetime import datetime

class DataSourceConfig(BaseModel):
    type: str
    description: Optional[str] = None
    data_format: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class DataSourceBase(BaseModel):
    name: str
    adapter_type: str
    config: DataSourceConfig

    model_config = ConfigDict(from_attributes=True)

class DataSourceCreate(DataSourceBase):
    pass

class DataSource(DataSourceBase):
    id: str
    container_id: str
    active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class DataSourceConfig(BaseModel):
    """Data source configuration model"""
    type: str
    adapter_type: str = "standard"
    data_format: Optional[str] = None
    description: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class DataSource(BaseModel):
    """Data source model matching Deep Lynx schema"""
    id: str
    container_id: str
    name: str
    adapter_type: str
    config: DataSourceConfig    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class ListDataSourcesResponse(BaseModel):
    """Response model for listing data sources"""
    value: List[DataSource]
    isError: bool = False
    error: Optional[Dict[str, Any]] = None

class CreateDataSourceResponse(BaseModel):
    """Response model for creating a data source"""
    value: DataSource
    isError: bool = False
    error: Optional[Dict[str, Any]] = None

class GetDataSourceResponse(BaseModel):
    """Response model for getting a single data source"""
    value: DataSource
    isError: bool = False
    error: Optional[Dict[str, Any]] = None

class UpdateDataSourceResponse(BaseModel):
    """Response model for updating a data source"""
    value: DataSource
    isError: bool = False
    error: Optional[Dict[str, Any]] = None

class Generic200Response(BaseModel):
    """Generic success response"""
    isError: bool = False
    error: Optional[Dict[str, Any]] = None
    value: Optional[Dict[str, Any]] = None 

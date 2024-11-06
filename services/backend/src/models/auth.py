from pydantic import BaseModel
from typing import Optional, Any, Dict

class DeepLynxAuth(BaseModel):
    """Authentication response from Deep Lynx"""
    token: str
    expiry: str
    # These are not required for the auth object
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    container_id: Optional[str] = None

class DeepLynxResponse(BaseModel):
    """Generic response wrapper for Deep Lynx operations"""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None 
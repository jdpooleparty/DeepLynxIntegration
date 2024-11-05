from pydantic import BaseModel
from typing import Optional

class DeepLynxAuth(BaseModel):
    api_key: str
    api_secret: str
    token: Optional[str] = None
    container_id: str

class DeepLynxResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None 
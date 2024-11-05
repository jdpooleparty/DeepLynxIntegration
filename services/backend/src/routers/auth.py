from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..auth.jwthandler import (
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get JWT token"""
    # Here you would typically validate against your database
    # For testing, we'll accept any username/password
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout():
    """Logout (client-side only)"""
    return {"message": "Successfully logged out"}
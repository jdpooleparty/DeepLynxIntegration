from fastapi import Request, HTTPException
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)

async def verify_auth(request: Request, call_next) -> Response:
    """
    Verify authentication headers and token
    
    Args:
        request: The incoming request
        call_next: The next middleware/handler in the chain
    """
    logger.debug(f"Verifying auth for path: {request.url.path}")
    
    # Get authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        logger.debug("No Authorization header found")
        raise HTTPException(
            status_code=401,
            detail="No authorization header"
        )

    # Verify Bearer token format
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != 'bearer':
            logger.debug(f"Invalid auth scheme: {scheme}")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme"
            )
    except ValueError:
        logger.debug("Invalid Authorization header format")
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )

    # For testing, accept any non-empty token
    if not token:
        logger.debug("Empty token provided")
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    logger.debug("Auth verification successful")
    return await call_next(request) 
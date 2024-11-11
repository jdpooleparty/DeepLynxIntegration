from .base_client import DeepLynxClient
import logging
from typing import List, Any

logger = logging.getLogger(__name__)

def invite_user(email: str, client: DeepLynxClient = None) -> bool:
    """Invite a user to join the container"""
    if not client:
        client = DeepLynxClient()
        
    if not client.authenticate():
        logger.error("Authentication failed")
        return False
        
    try:
        result = client.users_api.invite_user_to_container(
            container_id=client.container_id,
            body={"email": email}
        )
        logger.info(f"Successfully invited user {email} to container")
        return True
        
    except Exception as e:
        logger.error(f"Failed to invite user: {str(e)}")
        return False

def list_pending_invites(client: DeepLynxClient = None) -> List[Any]:
    """List all pending invites for the container"""
    if not client:
        client = DeepLynxClient()
        
    if not client.authenticate():
        logger.error("Authentication failed")
        return []
        
    try:
        invites = client.users_api.list_invited_users_for_container(
            container_id=client.container_id
        )
        if hasattr(invites, 'value') and invites.value:
            for invite in invites.value:
                logger.info(f"Pending invite: {invite.email}")
            return invites.value
        return []
        
    except Exception as e:
        logger.error(f"Failed to list invites: {str(e)}")
        return []

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    email = input("Enter email to invite: ")
    if invite_user(email):
        print("\nCurrent pending invites:")
        list_pending_invites() 
from .base_client import DeepLynxClient
import logging
from typing import List, Any

logger = logging.getLogger(__name__)

def assign_role(user_id: str, role: str = "user", client: DeepLynxClient = None) -> bool:
    """Assign a role to a user in the container"""
    if not client:
        client = DeepLynxClient()
        
    if not client.authenticate():
        logger.error("Authentication failed")
        return False
        
    try:
        # Check current roles first
        current_roles = list_user_roles(user_id, client)
        if role in current_roles:
            logger.info(f"User already has role: {role}")
            return True
            
        result = client.users_api.assign_user_role(
            container_id=client.container_id,
            user_id=user_id,
            body={"role": role}
        )
        logger.info(f"Successfully assigned role '{role}' to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to assign role: {str(e)}")
        return False

def list_user_roles(user_id: str, client: DeepLynxClient = None) -> List[str]:
    """List roles for a specific user"""
    if not client:
        client = DeepLynxClient()
        
    if not client.authenticate():
        logger.error("Authentication failed")
        return []
        
    try:
        roles = client.users_api.list_users_roles(
            container_id=client.container_id,
            user_id=user_id
        )
        
        if hasattr(roles, 'value') and roles.value:
            role_list = []
            for role in roles.value:
                if isinstance(role, str):
                    role_list.append(role)
                else:
                    role_list.append(getattr(role, 'name', 'Unknown'))
            return role_list
        return []
        
    except Exception as e:
        logger.error(f"Failed to list roles: {str(e)}")
        return []

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    user_id = input("Enter user ID: ")
    print("\nCurrent roles:")
    current_roles = list_user_roles(user_id)
    print(current_roles)
    
    role = input("\nEnter role to assign: ")
    if assign_role(user_id, role):
        print("\nUpdated roles:")
        print(list_user_roles(user_id)) 
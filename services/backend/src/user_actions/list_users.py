from user_actions.base_client import DeepLynxClient
import logging
from typing import List, Any, Dict

logger = logging.getLogger(__name__)

def list_container_users(client: DeepLynxClient = None) -> List[Dict[str, Any]]:
    """List all users in the container with detailed information"""
    if not client:
        client = DeepLynxClient()
        
    if not client.authenticate():
        logger.error("Authentication failed")
        return []
        
    try:
        users = client.users_api.list_users_for_container(
            container_id=client.container_id
        )
        
        if hasattr(users, 'value') and users.value:
            user_list = []
            for user in users.value:
                user_info = {
                    'id': user.id,
                    'name': user.display_name,
                    'email': user.email,
                    'active': user.active,
                    'admin': user.admin,
                    'provider': user.identity_provider,
                    'created_at': user.created_at,
                    'roles': list_user_roles(user.id, client)
                }
                user_list.append(user_info)
                logger.info(f"\nUser: {user.display_name}")
                logger.info(f"• ID: {user.id}")
                logger.info(f"• Email: {user.email}")
                logger.info(f"• Status: {'Active' if user.active else 'Inactive'}")
                logger.info(f"• Roles: {', '.join(user_info['roles'])}")
            return user_list
        return []
        
    except Exception as e:
        logger.error(f"Failed to list users: {str(e)}")
        return []

def list_user_roles(user_id: str, client: DeepLynxClient) -> List[str]:
    """Helper function to list user roles"""
    try:
        roles = client.users_api.list_users_roles(
            container_id=client.container_id,
            user_id=user_id
        )
        
        if hasattr(roles, 'value') and roles.value:
            return [role if isinstance(role, str) else getattr(role, 'name', 'Unknown') 
                   for role in roles.value]
        return []
        
    except Exception as e:
        logger.error(f"Failed to list roles for user {user_id}: {str(e)}")
        return []

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n=== Container Users ===")
    users = list_container_users()
    if not users:
        print("No users found in container") 
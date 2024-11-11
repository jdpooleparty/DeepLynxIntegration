from .base_client import DeepLynxClient
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def create_service_user(name: str, client: DeepLynxClient = None) -> Dict[str, Any]:
    """Create a new service user"""
    if not client:
        client = DeepLynxClient()
        
    if not client.authenticate():
        logger.error("Authentication failed")
        return {}
        
    try:
        result = client.users_api.create_service_user(
            container_id=client.container_id,
            body={"name": name}
        )
        
        if hasattr(result, 'value'):
            logger.info(f"Created service user: {name}")
            return {
                'id': result.value.id,
                'name': result.value.name,
                'created_at': result.value.created_at
            }
        return {}
        
    except Exception as e:
        logger.error(f"Failed to create service user: {str(e)}")
        return {}

def list_service_users(client: DeepLynxClient = None) -> List[Dict[str, Any]]:
    """List all service users in the container"""
    if not client:
        client = DeepLynxClient()
        
    if not client.authenticate():
        logger.error("Authentication failed")
        return []
        
    try:
        users = client.users_api.list_service_users(
            container_id=client.container_id
        )
        
        if hasattr(users, 'value') and users.value:
            service_users = []
            for user in users.value:
                user_info = {
                    'id': user.id,
                    'name': user.name,
                    'created_at': user.created_at
                }
                service_users.append(user_info)
                logger.info(f"Service User: {user.name} (ID: {user.id})")
            return service_users
        return []
        
    except Exception as e:
        logger.error(f"Failed to list service users: {str(e)}")
        return []

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    print("\n=== Service Users ===")
    service_users = list_service_users()
    
    if not service_users:
        name = input("\nNo service users found. Create one? Enter name (or press Enter to skip): ")
        if name:
            new_user = create_service_user(name)
            if new_user:
                print(f"\nCreated service user: {new_user['name']} (ID: {new_user['id']})") 
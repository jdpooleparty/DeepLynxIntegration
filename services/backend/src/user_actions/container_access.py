from .base_client import DeepLynxClient
import logging
from typing import List, Dict, Any
from deep_lynx.rest import ApiException

logger = logging.getLogger(__name__)

def list_available_containers(client: DeepLynxClient = None, include_all: bool = True) -> List[Dict[str, Any]]:
    """
    List all containers available in the system
    Args:
        client: DeepLynxClient instance
        include_all: If True, lists all containers regardless of membership. If False, lists only containers user is member of.
    """
    if not client:
        client = DeepLynxClient()
        
    if not client.authenticate():
        logger.error("Authentication failed")
        return []
        
    try:
        container_list = []
        
        # Get all containers using ContainersApi
        try:
            containers = client.containers_api.list_containers()
            logger.debug("Successfully accessed containers list")
            
            if hasattr(containers, 'value') and containers.value:
                for container in containers.value:
                    # Check membership by attempting to list users
                    is_member = False
                    try:
                        users = client.users_api.list_users_for_container(container_id=container.id)
                        if hasattr(users, 'value') and users.value:
                            is_member = True
                    except ApiException as e:
                        if e.status == 403:  # Permission denied means not a member
                            is_member = False
                        else:
                            logger.warning(f"Error checking container membership {container.id}: {e.reason}")
                    
                    container_info = {
                        'id': container.id,
                        'name': container.name,
                        'description': getattr(container, 'description', ''),
                        'active': getattr(container, 'active', False),
                        'is_member': is_member
                    }
                    container_list.append(container_info)
                    logger.info(f"Found container: {container.name} (ID: {container.id})")
            
        except ApiException as e:
            logger.error(f"Failed to list containers: {e.status} - {e.reason}")
            logger.debug(f"Response body: {e.body}")
            return []
            
        # If we only want containers the user is a member of, filter the list
        if not include_all:
            container_list = [c for c in container_list if c['is_member']]
            
        return container_list
            
    except Exception as e:
        logger.error(f"Failed to list containers: {str(e)}")
        logger.debug("Error details:", exc_info=True)
        return []

def assign_self_to_container(container_id: str, role: str = "admin", client: DeepLynxClient = None) -> bool:
    """Assign yourself to a container with specified role"""
    if not client:
        client = DeepLynxClient()
        
    if not client.authenticate():
        logger.error("Authentication failed")
        return False
        
    try:
        # First, get your own user ID
        me = client.users_api.retrieve_user_info()
        if not hasattr(me, 'value') or not me.value:
            logger.error("Could not retrieve user info")
            return False
            
        user_id = me.value.id
        logger.info(f"Retrieved user ID: {user_id}")
        
        # Attempt to assign role
        result = client.users_api.assign_user_role(
            container_id=container_id,
            user_id=user_id,
            body={"role": role}
        )
        
        logger.info(f"Successfully assigned role '{role}' to container {container_id}")
        return True
        
    except ApiException as e:
        if e.status == 403:
            logger.error("Permission denied: You may not have permission to assign roles")
        else:
            logger.error(f"API Error: {e.status} - {e.reason}")
        logger.debug(f"Response body: {e.body}")
        return False
    except Exception as e:
        logger.error(f"Failed to assign container access: {str(e)}")
        return False
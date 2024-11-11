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
        
        # Try to list all containers first (admin endpoint)
        try:
            containers = client.containers_api.list_containers()
            logger.debug("Successfully accessed admin container list")
            
            if hasattr(containers, 'value') and containers.value:
                for container in containers.value:
                    container_info = {
                        'id': container.id,
                        'name': container.name,
                        'description': getattr(container, 'description', ''),
                        'active': getattr(container, 'active', False),
                        'is_member': False  # Will be updated below
                    }
                    container_list.append(container_info)
                    logger.info(f"Found container: {container.name} (ID: {container.id})")
            
        except ApiException as e:
            if e.status == 403:
                logger.debug("Admin access denied, falling back to user containers")
            else:
                raise
        
        # Check membership for each container by trying to list users
        try:
            member_container_ids = set()
            for container in container_list:
                try:
                    # Try to list users for each container - this will only work for containers we're a member of
                    users = client.users_api.list_users_for_container(container_id=container['id'])
                    if hasattr(users, 'value') and users.value:
                        member_container_ids.add(container['id'])
                except ApiException as e:
                    if e.status != 403:  # Ignore permission denied errors
                        logger.warning(f"Error checking container {container['id']}: {e.reason}")
                    continue
                    
            # Update membership status
            for container in container_list:
                container['is_member'] = container['id'] in member_container_ids
                    
            # If we only want containers the user is a member of
            if not include_all:
                container_list = [c for c in container_list if c['is_member']]
                    
        except Exception as e:
            logger.warning(f"Could not verify container membership: {str(e)}")
            logger.debug("Error details:", exc_info=True)
            
        return container_list if container_list else []
            
    except ApiException as e:
        if e.status == 403:
            logger.error("Permission denied: You may not have sufficient permissions")
        else:
            logger.error(f"API Error: {e.status} - {e.reason}")
        logger.debug(f"Response body: {e.body}")
        return []
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
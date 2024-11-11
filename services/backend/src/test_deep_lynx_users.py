import deep_lynx
from deep_lynx.rest import ApiException
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepLynxUserTester:
    def __init__(self, host: str = None, env_file_path: str = None):
        """Initialize the Deep Lynx User Tester"""
        try:
            # Load environment variables
            if env_file_path:
                load_dotenv(env_file_path)
            else:
                load_dotenv()

            # Get configuration from environment
            self.host = host or os.getenv('DEEP_LYNX_URL')
            self.api_key = os.getenv('DEEP_LYNX_API_KEY')
            self.api_secret = os.getenv('DEEP_LYNX_API_SECRET')
            self.container_id = os.getenv('DEEP_LYNX_CONTAINER_ID')

            # Debug logging
            logger.debug("=== Deep Lynx User Tester Configuration ===")
            logger.debug(f"Host: {self.host}")
            logger.debug(f"Container ID: {self.container_id}")
            logger.debug(f"API Key present: {'Yes' if self.api_key else 'No'}")
            logger.debug(f"API Secret present: {'Yes' if self.api_secret else 'No'}")

            # Configure Deep Lynx client
            self.configuration = deep_lynx.Configuration()
            self.configuration.host = self.host
            
            # Set up authentication
            auth_str = f"{self.api_key}:{self.api_secret}"
            self.configuration.api_key['Authorization'] = auth_str
            self.configuration.api_key_prefix['Authorization'] = 'Basic'
            
            # Create API client
            self.api_client = deep_lynx.ApiClient(self.configuration)
            
            # Initialize Users API
            self.users_api = deep_lynx.UsersApi(self.api_client)
            self.auth_api = deep_lynx.AuthenticationApi(self.api_client)

        except Exception as e:
            logger.error(f"Failed to initialize Deep Lynx User Tester: {str(e)}")
            logger.debug("Error details:", exc_info=True)
            raise

    def authenticate(self) -> bool:
        """Authenticate with Deep Lynx"""
        try:
            logger.info("Attempting authentication...")
            token_response = self.auth_api.retrieve_o_auth_token(
                x_api_key=self.api_key,
                x_api_secret=self.api_secret
            )
            
            if isinstance(token_response, str):
                token = token_response
            elif hasattr(token_response, 'value'):
                token = token_response.value
            else:
                logger.error(f"Unexpected token response type: {type(token_response)}")
                return False
            
            self.api_client.default_headers['Authorization'] = f"Bearer {token}"
            logger.info("Successfully authenticated")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False

    def list_users(self) -> List[Any]:
        """List all users in the system"""
        try:
            logger.info("\n=== Listing All Users ===")
            logger.debug(f"Authorization header: {self.api_client.default_headers.get('Authorization', 'Not set')}")
            
            users = self.users_api.list_users()
            
            if hasattr(users, 'value') and users.value:
                logger.info(f"Found {len(users.value)} total users")
                for user in users.value:
                    # Log all available attributes for inspection
                    logger.info("\nUser Details:")
                    for attr in dir(user):
                        if not attr.startswith('_'):  # Skip internal attributes
                            value = getattr(user, attr, 'N/A')
                            logger.info(f"  • {attr}: {value}")
                return users.value
            return []
            
        except ApiException as e:
            logger.error(f"Failed to list users: {e.status} - {e.reason}")
            logger.debug(f"Response body: {e.body}")
            return []

    def list_container_users(self) -> List[Any]:
        """List all users in the container"""
        try:
            logger.info("\n=== Listing Container Users ===")
            users = self.users_api.list_users_for_container(
                container_id=self.container_id
            )
            
            if hasattr(users, 'value') and users.value:
                logger.info(f"Found {len(users.value)} users in container")
                for user in users.value:
                    logger.info("\nUser Details:")
                    logger.info(f"  • Name: {user.display_name}")
                    logger.info(f"  • Email: {user.email}")
                    logger.info(f"  • ID: {user.id}")
                    logger.info(f"  • Status: {'Active' if user.active else 'Inactive'}")
                    logger.info(f"  • Admin: {'Yes' if user.admin else 'No'}")
                    logger.info(f"  • Provider: {user.identity_provider}")
                    logger.info(f"  • Created: {user.created_at}")
                    
                    if user.permissions:
                        logger.info(f"  • Permissions: {len(user.permissions)}")
                    if user.roles:
                        logger.info(f"  • Roles: {len(user.roles)}")
                return users.value
            return []
            
        except ApiException as e:
            logger.error(f"Failed to list container users: {e.status} - {e.reason}")
            logger.debug(f"Response body: {e.body}")
            return []

    def list_service_users(self) -> List[Any]:
        """List all service users in the container"""
        try:
            logger.info("\n=== Listing Service Users ===")
            users = self.users_api.list_service_users(
                container_id=self.container_id
            )
            
            if hasattr(users, 'value') and users.value:
                logger.info(f"Found {len(users.value)} service users")
                for user in users.value:
                    logger.debug(f"Service User: {user.name} (ID: {user.id})")
                return users.value
            return []
            
        except ApiException as e:
            logger.error(f"Failed to list service users: {e.status} - {e.reason}")
            logger.debug(f"Response body: {e.body}")
            return []

    def list_user_roles(self, user_id: str) -> List[Any]:
        """List roles for a specific user in the container"""
        try:
            logger.info(f"\n=== Listing Roles for User {user_id} ===")
            roles = self.users_api.list_users_roles(
                container_id=self.container_id,
                user_id=user_id
            )
            
            if hasattr(roles, 'value') and roles.value:
                logger.info(f"Found {len(roles.value)} roles")
                for role in roles.value:
                    if isinstance(role, str):
                        logger.info(f"  • Role: {role}")
                    else:
                        logger.info(f"  • Role Name: {getattr(role, 'name', 'Unknown')}")
                        logger.info(f"  • Role ID: {getattr(role, 'id', 'Unknown')}")
                        if hasattr(role, 'description'):
                            logger.info(f"  • Description: {role.description}")
                return roles.value
            return []
            
        except ApiException as e:
            logger.error(f"Failed to list user roles: {e.status} - {e.reason}")
            logger.debug(f"Response body: {e.body}")
            return []

    def list_container_invites(self) -> List[Any]:
        """List all pending invites for the container"""
        try:
            logger.info("\n=== Listing Container Invites ===")
            invites = self.users_api.list_invited_users_for_container(
                container_id=self.container_id
            )
            
            if hasattr(invites, 'value') and invites.value:
                logger.info(f"Found {len(invites.value)} pending invites")
                for invite in invites.value:
                    logger.debug(f"Invite: {invite.email}")
                return invites.value
            return []
            
        except ApiException as e:
            logger.error(f"Failed to list invites: {e.status} - {e.reason}")
            logger.debug(f"Response body: {e.body}")
            return []

    def invite_user_to_container(self, email: str) -> bool:
        """Invite a user to join the container"""
        try:
            logger.info(f"\n=== Inviting User {email} to Container ===")
            result = self.users_api.invite_user_to_container(
                container_id=self.container_id,
                body={"email": email}
            )
            
            logger.info(f"Successfully invited user {email} to container")
            logger.debug(f"Invite result: {result}")
            return True
            
        except ApiException as e:
            logger.error(f"Failed to invite user: {e.status} - {e.reason}")
            logger.debug(f"Response body: {e.body}")
            return False

    def assign_user_to_container(self, user_id: str, role: str = "user") -> bool:
        """Directly assign a user to the container with a role"""
        try:
            logger.info(f"\n=== Assigning User {user_id} to Container ===")
            
            # First, check if user already has roles
            current_roles = self.list_user_roles(user_id)
            if role in current_roles:
                logger.info(f"User already has role: {role}")
                return True
            
            # Assign the role to the user
            result = self.users_api.assign_user_role(
                container_id=self.container_id,
                user_id=user_id,
                body={"role": role}
            )
            
            logger.info(f"Successfully assigned user {user_id} to container with role: {role}")
            logger.debug(f"Assignment result: {result}")
            return True
            
        except ApiException as e:
            logger.error(f"Failed to assign user: {e.status} - {e.reason}")
            logger.debug(f"Response body: {e.body}")
            return False

def main():
    """Main test execution"""
    try:
        # Initialize tester
        tester = DeepLynxUserTester(
            env_file_path=os.path.join(os.path.dirname(__file__), '..', '.env')
        )
        
        # Authenticate
        if not tester.authenticate():
            logger.error("Authentication failed")
            return
        
        logger.info("\n=== Starting User Management Tests ===")
        
        # 1. First, list existing users to see current state
        logger.info("\n=== Current Container Users ===")
        current_users = tester.list_container_users()
        
        # 2. Invite a new user
        new_user_email = "test.user@example.com"  # Replace with actual email
        logger.info(f"\n=== Inviting New User: {new_user_email} ===")
        if tester.invite_user_to_container(new_user_email):
            logger.info(f"✓ Successfully sent invitation to {new_user_email}")
            
            # Check pending invites
            invites = tester.list_container_invites()
            logger.info(f"Current pending invites: {len(invites)}")
        
        # 3. Assign roles to existing user
        # Using the ID we got from listing users
        for user in current_users:
            user_id = user.id
            user_name = user.display_name
            
            logger.info(f"\n=== Managing User: {user_name} ===")
            
            # List current roles
            current_roles = tester.list_user_roles(user_id)
            logger.info(f"Current roles: {current_roles}")
            
            # Assign a new role if they don't have it
            new_role = "user"  # Can be 'admin', 'user', or other roles defined in your system
            if new_role not in current_roles:
                if tester.assign_user_to_container(user_id, new_role):
                    logger.info(f"✓ Successfully assigned '{new_role}' role to {user_name}")
                    
                    # Verify the new role assignment
                    updated_roles = tester.list_user_roles(user_id)
                    logger.info(f"Updated roles: {updated_roles}")
            else:
                logger.info(f"User already has '{new_role}' role")
        
        # 4. List service users (if any)
        service_users = tester.list_service_users()
        if service_users:
            logger.info("\n=== Service Users ===")
            for service_user in service_users:
                logger.info(f"• Service User: {service_user.name} (ID: {service_user.id})")
        else:
            logger.info("\nNo service users found")
        
        # 5. Final verification of all users and their roles
        logger.info("\n=== Final User Status ===")
        final_users = tester.list_container_users()
        for user in final_users:
            logger.info(f"\nUser: {user.display_name}")
            logger.info(f"• ID: {user.id}")
            logger.info(f"• Email: {user.email}")
            logger.info(f"• Status: {'Active' if user.active else 'Inactive'}")
            
            roles = tester.list_user_roles(user.id)
            logger.info(f"• Roles: {', '.join(roles) if roles else 'None'}")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        logger.debug("Error details:", exc_info=True)
    finally:
        logger.info("\n=== User Management Tests Complete ===")

if __name__ == "__main__":
    # Set logging to DEBUG to see more details
    logging.basicConfig(level=logging.DEBUG)
    main() 
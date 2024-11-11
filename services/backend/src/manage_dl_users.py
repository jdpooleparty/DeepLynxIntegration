import logging
from user_actions.list_users import list_container_users
from user_actions.invite_user import invite_user, list_pending_invites
from user_actions.manage_roles import assign_role
from user_actions.service_users import create_service_user, list_service_users
from user_actions.container_access import list_available_containers, assign_self_to_container
from user_actions.base_client import DeepLynxClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def display_container_menu(client: DeepLynxClient):
    """Handle container management menu"""
    while True:
        print("\nContainer Access Management")
        print("1. List all containers")
        print("2. List my containers")
        print("3. Assign self to container")
        print("4. Back to main menu")
        
        container_choice = input("\nEnter your choice (1-4): ")
        
        try:
            if container_choice == "1":
                containers = list_available_containers(client, include_all=True)
                if containers:
                    print("\nAll Available Containers:")
                    for container in containers:
                        print(f"\n• {container['name']} (ID: {container['id']})")
                        print(f"  Status: {'Active' if container['active'] else 'Inactive'}")
                        print(f"  Member: {'Yes' if container['is_member'] else 'No'}")
                        if container.get('description'):
                            print(f"  Description: {container['description']}")
                else:
                    print("No containers found")
                    
            elif container_choice == "2":
                containers = list_available_containers(client, include_all=False)
                if containers:
                    print("\nMy Containers:")
                    for container in containers:
                        if container['is_member']:
                            print(f"\n• {container['name']} (ID: {container['id']})")
                            print(f"  Status: {'Active' if container['active'] else 'Inactive'}")
                            if container.get('description'):
                                print(f"  Description: {container['description']}")
                else:
                    print("No containers found")
                    
            elif container_choice == "3":
                containers = list_available_containers(client)
                if containers:
                    print("\nAvailable Containers:")
                    active_containers = [c for c in containers if c['active']]
                    for i, container in enumerate(active_containers, 1):
                        print(f"{i}. {container['name']} (ID: {container['id']})")
                        print(f"   Current member: {'Yes' if container['is_member'] else 'No'}")
                    
                    idx = int(input("\nSelect container number: ")) - 1
                    if 0 <= idx < len(active_containers):
                        container = active_containers[idx]
                        print("\nAvailable roles: admin, user")
                        role = input("Enter role to assign (default: admin): ").strip() or "admin"
                        
                        if assign_self_to_container(container['id'], role, client):
                            print(f"\nSuccessfully assigned yourself to container: {container['name']}")
                            print("Note: You may need to re-authenticate to access the container")
                        else:
                            print("\nFailed to assign container access")
                else:
                    print("No containers available")
                    
            elif container_choice == "4":
                break
                
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}")

def main():
    # Create a shared client instance
    client = DeepLynxClient()
    
    while True:
        print("\nDeep Lynx User Management")
        print("1. List all users")
        print("2. Invite new user")
        print("3. Manage user roles")
        print("4. Manage service users")
        print("5. Container Access Management")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ")
        
        try:
            if choice == "1":
                users = list_container_users(client)
                if users:
                    print("\nContainer Users:")
                    for user in users:
                        print(f"\nUser: {user['name']}")
                        print(f"Email: {user['email']}")
                        print(f"ID: {user['id']}")
                        print(f"Active: {'Yes' if user['active'] else 'No'}")
                        print(f"Admin: {'Yes' if user['admin'] else 'No'}")
                else:
                    print("No users found")
                    
            elif choice == "2":
                email = input("Enter email to invite: ")
                if invite_user(email, client):
                    print(f"Successfully invited {email}")
                    print("\nCurrent pending invites:")
                    invites = list_pending_invites(client)
                    for invite in invites:
                        print(f"• {invite.email}")
                        
            elif choice == "3":
                users = list_container_users(client)
                if users:
                    print("\nAvailable users:")
                    for i, user in enumerate(users, 1):
                        print(f"{i}. {user['name']} ({user['email']})")
                    
                    idx = int(input("\nSelect user number: ")) - 1
                    if 0 <= idx < len(users):
                        user = users[idx]
                        print("\nAvailable roles: admin, user")
                        role = input("Enter role to assign: ")
                        if assign_role(user['id'], role, client):
                            print(f"Successfully assigned role '{role}' to {user['name']}")
                else:
                    print("No users available")
                    
            elif choice == "4":
                print("\nService Users:")
                service_users = list_service_users(client)
                if service_users:
                    for user in service_users:
                        print(f"• {user['name']} (ID: {user['id']})")
                    
                create_new = input("\nCreate new service user? (y/n): ")
                if create_new.lower() == 'y':
                    name = input("Enter service user name: ")
                    result = create_service_user(name, client)
                    if result:
                        print(f"Created service user: {result['name']} (ID: {result['id']})")
                        
            elif choice == "5":
                display_container_menu(client)
            elif choice == "6":
                break
                
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}")

if __name__ == "__main__":
    main() 
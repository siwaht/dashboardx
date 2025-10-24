#!/usr/bin/env python3
"""
User Management System Test Script

Tests the user management functionality including:
- Admin authentication
- User CRUD operations
- Permission checks
- Role assignments
"""

import requests
import json
import sys
from typing import Dict, Optional

# Configuration
BACKEND_URL = "http://localhost:8000"
ADMIN_EMAIL = "cc@siwaht.com"
ADMIN_PASSWORD = "Hola173!"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")

def print_test(text: str):
    """Print test name"""
    print(f"\n{Colors.BOLD}Testing: {text}{Colors.END}")

class UserManagementTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.jwt_token: Optional[str] = None
        self.test_user_id: Optional[str] = None
        self.passed_tests = 0
        self.failed_tests = 0
    
    def run_all_tests(self):
        """Run all tests"""
        print_header("User Management System Tests")
        
        # Test 1: Backend Health Check
        if not self.test_backend_health():
            print_error("Backend is not running. Please start the backend server.")
            return False
        
        # Test 2: Admin Login
        if not self.test_admin_login():
            print_error("Admin login failed. Cannot proceed with other tests.")
            return False
        
        # Test 3: Get Current User
        self.test_get_current_user()
        
        # Test 4: List Users
        self.test_list_users()
        
        # Test 5: Create User
        self.test_create_user()
        
        # Test 6: Get Specific User
        if self.test_user_id:
            self.test_get_user()
        
        # Test 7: Update User
        if self.test_user_id:
            self.test_update_user()
        
        # Test 8: Update User Status
        if self.test_user_id:
            self.test_update_user_status()
        
        # Test 9: Delete User
        if self.test_user_id:
            self.test_delete_user()
        
        # Print Summary
        self.print_summary()
        
        return self.failed_tests == 0
    
    def test_backend_health(self) -> bool:
        """Test if backend is running"""
        print_test("Backend Health Check")
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print_success(f"Backend is healthy: {data.get('status')}")
                print_info(f"Version: {data.get('version')}")
                self.passed_tests += 1
                return True
            else:
                print_error(f"Backend returned status code: {response.status_code}")
                self.failed_tests += 1
                return False
        except requests.exceptions.RequestException as e:
            print_error(f"Cannot connect to backend: {e}")
            self.failed_tests += 1
            return False
    
    def test_admin_login(self) -> bool:
        """Test admin login via Supabase"""
        print_test("Admin Login")
        print_info("Note: This test requires Supabase to be configured")
        print_info(f"Attempting to login as: {ADMIN_EMAIL}")
        
        # For this test, we'll assume the JWT token is provided
        # In a real scenario, you would authenticate via Supabase client
        print_info("Please provide the JWT token for the admin user")
        print_info("You can get this from:")
        print_info("1. Login to the frontend application")
        print_info("2. Open browser DevTools > Application > Local Storage")
        print_info("3. Find 'supabase.auth.token' and copy the access_token")
        
        token = input(f"\n{Colors.YELLOW}Enter JWT token (or press Enter to skip): {Colors.END}").strip()
        
        if not token:
            print_info("Skipping authentication tests (no token provided)")
            print_info("You can still test by manually setting the token")
            self.failed_tests += 1
            return False
        
        self.jwt_token = token
        
        # Test the token by calling /api/users/me
        try:
            headers = {"Authorization": f"Bearer {self.jwt_token}"}
            response = requests.get(f"{self.backend_url}/api/users/me", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                print_success(f"Authenticated as: {user_data.get('email')}")
                print_info(f"Role: {user_data.get('role')}")
                print_info(f"Tenant ID: {user_data.get('tenant_id')}")
                
                if user_data.get('role') == 'admin':
                    print_success("User has admin role")
                    self.passed_tests += 1
                    return True
                else:
                    print_error("User does not have admin role")
                    self.failed_tests += 1
                    return False
            else:
                print_error(f"Authentication failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed_tests += 1
                return False
        except Exception as e:
            print_error(f"Error during authentication: {e}")
            self.failed_tests += 1
            return False
    
    def test_get_current_user(self):
        """Test getting current user profile"""
        print_test("Get Current User Profile")
        
        if not self.jwt_token:
            print_info("Skipping (no JWT token)")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.jwt_token}"}
            response = requests.get(f"{self.backend_url}/api/users/me", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                print_success("Successfully retrieved user profile")
                print_info(f"Email: {user_data.get('email')}")
                print_info(f"Full Name: {user_data.get('full_name')}")
                print_info(f"Role: {user_data.get('role')}")
                print_info(f"Active: {user_data.get('is_active')}")
                self.passed_tests += 1
            else:
                print_error(f"Failed to get user profile: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed_tests += 1
        except Exception as e:
            print_error(f"Error: {e}")
            self.failed_tests += 1
    
    def test_list_users(self):
        """Test listing all users"""
        print_test("List All Users")
        
        if not self.jwt_token:
            print_info("Skipping (no JWT token)")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.jwt_token}"}
            response = requests.get(f"{self.backend_url}/api/users", headers=headers)
            
            if response.status_code == 200:
                users = response.json()
                print_success(f"Successfully retrieved {len(users)} users")
                for user in users[:3]:  # Show first 3 users
                    print_info(f"  - {user.get('email')} ({user.get('role')})")
                if len(users) > 3:
                    print_info(f"  ... and {len(users) - 3} more")
                self.passed_tests += 1
            else:
                print_error(f"Failed to list users: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed_tests += 1
        except Exception as e:
            print_error(f"Error: {e}")
            self.failed_tests += 1
    
    def test_create_user(self):
        """Test creating a new user"""
        print_test("Create New User")
        
        if not self.jwt_token:
            print_info("Skipping (no JWT token)")
            return
        
        try:
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json"
            }
            
            user_data = {
                "email": "test.user@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User",
                "role": "user"
            }
            
            response = requests.post(
                f"{self.backend_url}/api/users",
                headers=headers,
                json=user_data
            )
            
            if response.status_code == 201:
                created_user = response.json()
                self.test_user_id = created_user.get('id')
                print_success("Successfully created user")
                print_info(f"User ID: {self.test_user_id}")
                print_info(f"Email: {created_user.get('email')}")
                print_info(f"Role: {created_user.get('role')}")
                self.passed_tests += 1
            else:
                print_error(f"Failed to create user: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed_tests += 1
        except Exception as e:
            print_error(f"Error: {e}")
            self.failed_tests += 1
    
    def test_get_user(self):
        """Test getting a specific user"""
        print_test("Get Specific User")
        
        if not self.jwt_token or not self.test_user_id:
            print_info("Skipping (no JWT token or user ID)")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.jwt_token}"}
            response = requests.get(
                f"{self.backend_url}/api/users/{self.test_user_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                print_success("Successfully retrieved user")
                print_info(f"Email: {user_data.get('email')}")
                print_info(f"Role: {user_data.get('role')}")
                self.passed_tests += 1
            else:
                print_error(f"Failed to get user: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed_tests += 1
        except Exception as e:
            print_error(f"Error: {e}")
            self.failed_tests += 1
    
    def test_update_user(self):
        """Test updating a user"""
        print_test("Update User")
        
        if not self.jwt_token or not self.test_user_id:
            print_info("Skipping (no JWT token or user ID)")
            return
        
        try:
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json"
            }
            
            update_data = {
                "full_name": "Updated Test User",
                "role": "viewer"
            }
            
            response = requests.put(
                f"{self.backend_url}/api/users/{self.test_user_id}",
                headers=headers,
                json=update_data
            )
            
            if response.status_code == 200:
                updated_user = response.json()
                print_success("Successfully updated user")
                print_info(f"New Name: {updated_user.get('full_name')}")
                print_info(f"New Role: {updated_user.get('role')}")
                self.passed_tests += 1
            else:
                print_error(f"Failed to update user: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed_tests += 1
        except Exception as e:
            print_error(f"Error: {e}")
            self.failed_tests += 1
    
    def test_update_user_status(self):
        """Test updating user status"""
        print_test("Update User Status")
        
        if not self.jwt_token or not self.test_user_id:
            print_info("Skipping (no JWT token or user ID)")
            return
        
        try:
            headers = {
                "Authorization": f"Bearer {self.jwt_token}",
                "Content-Type": "application/json"
            }
            
            # Disable user
            response = requests.patch(
                f"{self.backend_url}/api/users/{self.test_user_id}/status",
                headers=headers,
                json={"is_active": False}
            )
            
            if response.status_code == 200:
                updated_user = response.json()
                print_success("Successfully disabled user")
                print_info(f"Active Status: {updated_user.get('is_active')}")
                
                # Re-enable user
                response = requests.patch(
                    f"{self.backend_url}/api/users/{self.test_user_id}/status",
                    headers=headers,
                    json={"is_active": True}
                )
                
                if response.status_code == 200:
                    print_success("Successfully re-enabled user")
                    self.passed_tests += 1
                else:
                    print_error("Failed to re-enable user")
                    self.failed_tests += 1
            else:
                print_error(f"Failed to update user status: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed_tests += 1
        except Exception as e:
            print_error(f"Error: {e}")
            self.failed_tests += 1
    
    def test_delete_user(self):
        """Test deleting a user"""
        print_test("Delete User")
        
        if not self.jwt_token or not self.test_user_id:
            print_info("Skipping (no JWT token or user ID)")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.jwt_token}"}
            response = requests.delete(
                f"{self.backend_url}/api/users/{self.test_user_id}",
                headers=headers
            )
            
            if response.status_code == 204:
                print_success("Successfully deleted user")
                self.passed_tests += 1
            else:
                print_error(f"Failed to delete user: {response.status_code}")
                print_error(f"Response: {response.text}")
                self.failed_tests += 1
        except Exception as e:
            print_error(f"Error: {e}")
            self.failed_tests += 1
    
    def print_summary(self):
        """Print test summary"""
        print_header("Test Summary")
        
        total_tests = self.passed_tests + self.failed_tests
        
        print(f"Total Tests: {total_tests}")
        print_success(f"Passed: {self.passed_tests}")
        
        if self.failed_tests > 0:
            print_error(f"Failed: {self.failed_tests}")
        else:
            print_success("All tests passed! ✨")
        
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")

def main():
    """Main function"""
    tester = UserManagementTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

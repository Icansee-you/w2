"""
Script to create test accounts with default preferences.
Run this once to set up the 5 test accounts.
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from supabase_client import get_supabase_client
from categorization_engine import get_all_categories

def create_test_accounts():
    """Create 5 test accounts with default preferences."""
    supabase = get_supabase_client()
    
    # Test accounts to create
    accounts = [
        {"name": "Anna", "email": "mharebel@gmail.com"},
        {"name": "Chris", "email": "chris_huls@hotmail.com"},
        {"name": "Bert", "email": "bert123456789@gmail.com"},
        {"name": "Dodo", "email": "dodo123456789@gmail.com"},
        {"name": "Epistel", "email": "epistel123456789@gmail.com"},
    ]
    
    password = "password"
    all_categories = get_all_categories()
    
    print("=" * 60)
    print("Creating Test Accounts")
    print("=" * 60)
    print()
    
    for account in accounts:
        name = account["name"]
        email = account["email"]
        
        print(f"Creating account for {name} ({email})...")
        
        # Try to sign up
        result = supabase.sign_up(email, password)
        
        if result.get('success'):
            user = result.get('user')
            user_id = user.id if hasattr(user, 'id') else str(user)
            
            print(f"  [OK] Account created successfully")
            print(f"  User ID: {user_id}")
            
            # Sign in as this user to set preferences (needed for RLS)
            sign_in_result = supabase.sign_in(email, password)
            if sign_in_result.get('success'):
                # Set default preferences: no blacklist, all categories
                success = supabase.update_user_preferences(
                    user_id=user_id,
                    blacklist_keywords=[],  # No blacklist
                    selected_categories=all_categories  # All categories
                )
                
                if success:
                    print(f"  [OK] Preferences set: no blacklist, all categories")
                else:
                    print(f"  [WARNING] Could not set preferences")
            else:
                print(f"  [WARNING] Could not sign in to set preferences")
                
        else:
            error = result.get('error', 'Unknown error')
            if 'already registered' in error.lower() or 'already exists' in error.lower():
                print(f"  [INFO] Account already exists, updating preferences...")
                
                # Try to sign in to get user ID
                sign_in_result = supabase.sign_in(email, password)
                if sign_in_result.get('success'):
                    user = sign_in_result.get('user')
                    user_id = user.id if hasattr(user, 'id') else str(user)
                    
                    # Update preferences
                    success = supabase.update_user_preferences(
                        user_id=user_id,
                        blacklist_keywords=[],
                        selected_categories=all_categories
                    )
                    
                    if success:
                        print(f"  [OK] Preferences updated: no blacklist, all categories")
                    else:
                        print(f"  [WARNING] Could not update preferences")
                else:
                    print(f"  [ERROR] Could not sign in to update preferences")
            else:
                print(f"  [ERROR] Failed to create account: {error}")
        
        print()
    
    print("=" * 60)
    print("Account creation complete!")
    print("=" * 60)
    print()
    print("You can now log in with:")
    print("  Anna: mharebel@gmail.com")
    print("  Chris: chris_huls@hotmail.com")
    print("  Bert: bert123456789@gmail.com")
    print("  Dodo: dodo123456789@gmail.com")
    print("  Epistel: epistel123456789@gmail.com")
    print("  Password for all: password")
    print()

if __name__ == "__main__":
    create_test_accounts()


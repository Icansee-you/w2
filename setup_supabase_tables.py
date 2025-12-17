"""
Script to set up Supabase tables.
Run this once after creating your Supabase project.
"""
import os
from supabase import create_client, Client

def setup_supabase_tables():
    """Set up Supabase tables by running SQL schema."""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Use service role key for admin operations
    
    if not supabase_url or not supabase_service_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        return False
    
    client: Client = create_client(supabase_url, supabase_service_key)
    
    # Read SQL schema file
    try:
        with open('supabase_schema.sql', 'r', encoding='utf-8') as f:
            sql_schema = f.read()
        
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in sql_schema.split(';') if s.strip() and not s.strip().startswith('--')]
        
        print("Setting up Supabase tables...")
        for statement in statements:
            if statement:
                try:
                    # Use RPC or direct SQL execution
                    # Note: Supabase Python client doesn't directly support raw SQL
                    # You'll need to run the SQL in Supabase dashboard SQL editor instead
                    print(f"Would execute: {statement[:50]}...")
                except Exception as e:
                    print(f"Error executing statement: {e}")
        
        print("\n⚠️  Note: Supabase Python client doesn't support raw SQL execution.")
        print("Please run the SQL from 'supabase_schema.sql' in your Supabase dashboard:")
        print("1. Go to your Supabase project")
        print("2. Click 'SQL Editor'")
        print("3. Paste the contents of supabase_schema.sql")
        print("4. Click 'Run'")
        
        return True
    except FileNotFoundError:
        print("Error: supabase_schema.sql not found")
        return False

if __name__ == "__main__":
    setup_supabase_tables()


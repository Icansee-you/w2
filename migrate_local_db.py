"""
Migration script to add 'categories' column to local SQLite database.
Run this once to update your existing local_test.db file.
"""
import sqlite3
import os

def migrate_database():
    """Add categories column to articles table if it doesn't exist."""
    db_path = "local_test.db"
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. It will be created automatically on first run.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if categories column exists
        cursor.execute("PRAGMA table_info(articles)")
        columns = [row[1] for row in cursor.fetchall()]
        
        needs_migration = False
        
        if 'categories' not in columns:
            print("Adding 'categories' column to articles table...")
            cursor.execute("ALTER TABLE articles ADD COLUMN categories TEXT")
            needs_migration = True
        
        if 'eli5_llm' not in columns:
            print("Adding 'eli5_llm' column to articles table...")
            cursor.execute("ALTER TABLE articles ADD COLUMN eli5_llm TEXT")
            needs_migration = True
        
        if needs_migration:
            conn.commit()
            print("✓ Migration complete!")
        else:
            print("✓ Database is up to date. No migration needed.")
        
        conn.close()
    except Exception as e:
        print(f"Error migrating database: {e}")
        print("You may need to delete local_test.db and let it recreate automatically.")

if __name__ == "__main__":
    migrate_database()


#!/usr/bin/env python3
"""
Database Schema Migration Runner
Runs migrations for all detected databases
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from schema_migrator import SchemaMigrator
except ImportError as e:
    print(f"❌ Could not import SchemaMigrator: {e}")
    sys.exit(1)

def main():
    """Run migrations for all databases"""
    
    # Get configuration from environment
    base_dir = os.environ.get('BASE', '/opt/ecapps-hosting')
    db_host = os.environ.get('DB_HOST', 'main_db')
    db_user = os.environ.get('DB_ROOT_USER', 'root')
    db_pass = os.environ.get('DB_ROOT_PASS', '')
    
    schemas_dir = os.path.join(base_dir, 'data', 'schemas')
    
    print("🔄 Starting schema migrations...\n")
    
    # Check if schemas directory exists
    if not os.path.isdir(schemas_dir):
        print("ℹ️ No schema files found to migrate")
        return 0
    
    # Track overall success
    all_success = True
    migration_count = 0
    
    # Iterate through each database directory
    for db_dir in sorted(os.listdir(schemas_dir)):
        db_path = os.path.join(schemas_dir, db_dir)
        
        # Skip if not a directory
        if not os.path.isdir(db_path):
            continue
        
        db_name = db_dir
        schema_dir = db_path
        migration_count += 1
        
        print(f"   🔧 Migrating database: {db_name}")
        
        try:
            # Create migrator instance
            migrator = SchemaMigrator(
                db_host=db_host,
                db_user=db_user,
                db_pass=db_pass,
                db_name=db_name
            )
            
            # Run migration
            success = migrator.migrate(schema_dir)
            
            if success:
                print(f"   ✅ Migration completed for {db_name}\n")
            else:
                print(f"   ⚠️ Migration encountered issues for {db_name} (check logs)\n")
                all_success = False
                
        except Exception as e:
            print(f"   ❌ Error migrating {db_name}: {e}\n")
            all_success = False
    
    # Final summary
    if migration_count == 0:
        print("ℹ️ No databases found to migrate")
        return 0
    
    if all_success:
        print(f"✅ All {migration_count} migration(s) completed successfully!")
        return 0
    else:
        print(f"⚠️ {migration_count} migration(s) completed with issues")
        return 1

if __name__ == '__main__':
    sys.exit(main())

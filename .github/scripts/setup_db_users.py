#!/usr/bin/env python3
"""
Database Users Setup
Creates database users with proper permissions before migrations
Accepts secrets as JSON array argument for clarity and no guessing
"""

import sys
import os
import json
import mysql.connector
from pathlib import Path

def setup_db_users(available_secrets):
    """Create database users from db-config.json files
    
    Args:
        available_secrets: List of secret names available in environment
    """
    print("\n" + "="*70)
    print("👤 DATABASE USER SETUP - INITIALIZATION")
    print("="*70 + "\n")
    
    # Get configuration from environment
    base_dir = os.environ.get('BASE', '/opt/ecapps-hosting')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_user = os.environ.get('DB_ROOT_USER', 'root')
    db_pass = os.environ.get('DB_ROOT_PASS', '')
    
    print("[DEBUG] Environment Configuration:")
    print(f"  - BASE_DIR: {base_dir}")
    print(f"  - DB_HOST: {db_host}")
    print(f"  - DB_ROOT_USER: {db_user}")
    print(f"  - DB_ROOT_PASS: {'***' if db_pass else 'NOT SET'}")
    print(f"  - Available secrets: {len(available_secrets)} total\n")
    
    schemas_dir = os.path.join(base_dir, 'data', 'schemas')
    
    print(f"[DEBUG] Schemas directory path: {schemas_dir}")
    print(f"[DEBUG] Available secrets: {available_secrets}\n")
    
    # Check if schemas directory exists
    print("[STEP 1] Checking schemas directory...")
    if not os.path.isdir(schemas_dir):
        print(f"  ⚠️ WARN: Schemas directory does not exist: {schemas_dir}")
        print("  ℹ️ This is OK if no databases have been synced yet")
        print("  → Returning 0 (no databases to setup)\n")
        return 0
    
    print(f"  ✅ Schemas directory exists\n")
    
    # List what's in the schemas directory for debugging
    print("[STEP 2] Scanning schemas directory...")
    try:
        items = os.listdir(schemas_dir)
        print(f"  📋 Found {len(items)} item(s) in {schemas_dir}")
        for item in items:
            item_path = os.path.join(schemas_dir, item)
            if os.path.isdir(item_path):
                print(f"     📁 {item}/")
                # List config file if exists
                config_check = os.path.join(item_path, 'db-config.json')
                if os.path.isfile(config_check):
                    print(f"        └─ db-config.json ✓")
            else:
                print(f"     📄 {item}")
        print()
    except Exception as e:
        print(f"  ❌ ERROR: Could not list schemas directory: {e}")
        return 1
    
    print("[STEP 3] Connecting to MySQL...")
    try:
        print(f"  Attempting connection to {db_host} as {db_user}...")
        # Connect to MySQL as root
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            autocommit=True
        )
        cursor = connection.cursor()
        print(f"  ✅ SUCCESS: Connected to MySQL at {db_host}\n")
        
    except mysql.connector.Error as e:
        print(f"  ❌ FAILURE: Cannot connect to MySQL")
        print(f"     Error: {e}")
        print(f"     Host: {db_host}, User: {db_user}")
        print(f"     → Ensure MariaDB container is running and healthy\n")
        return 1
    
    users_created = 0
    users_skipped = 0
    missing_secrets = []
    
    print("[STEP 4] Processing database configurations...\n")
    
    # Iterate through each database directory
    db_dirs = sorted(os.listdir(schemas_dir))
    print(f"  Found {len(db_dirs)} directories to process\n")
    
    for idx, db_dir in enumerate(db_dirs, 1):
        db_path = os.path.join(schemas_dir, db_dir)
        config_file = os.path.join(db_path, 'db-config.json')
        
        # Skip if not a directory or no config file
        print(f"  [{idx}] Processing: {db_dir}")
        if not os.path.isdir(db_path):
            print(f"       ↭️  SKIP: Not a directory\n")
            continue
            
        if not os.path.isfile(config_file):
            print(f"       ↭️  SKIP: No db-config.json found\n")
            continue
        
        print(f"       ✓ Found db-config.json")
        
        # Read config
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"       ✓ Config parsed successfully")
        except Exception as e:
            print(f"       ❌ SKIP: Cannot parse config: {e}\n")
            users_skipped += 1
            continue
        
        db_name = config.get('database_name')
        db_user_name = config.get('database_user')
        secret_name = config.get('secret_name')
        
        print(f"       - DB Name: {db_name}")
        print(f"       - DB User: {db_user_name}")
        print(f"       - Secret: {secret_name}")
        
        if not db_name or not db_user_name or not secret_name:
            print(f"       ❌ SKIP: Incomplete config")
            if not db_name: print(f"          Missing: database_name")
            if not db_user_name: print(f"          Missing: database_user")
            if not secret_name: print(f"          Missing: secret_name")
            print()
            users_skipped += 1
            continue
        
        # Check if secret is in available list
        if secret_name not in available_secrets:
            print(f"       ❌ SKIP: Secret '{secret_name}' NOT in available secrets list")
            print(f"          Available: {available_secrets}\n")
            missing_secrets.append(secret_name)
            users_skipped += 1
            continue
        
        print(f"       ✓ Secret '{secret_name}' is in available list")
        
        # Get password from environment variable
        db_user_pass = os.environ.get(secret_name)
        
        if not db_user_pass:
            print(f"       ❌ SKIP: Secret '{secret_name}' exists in list but NOT in environment")
            print(f"          Check GitHub Secrets configuration\n")
            missing_secrets.append(secret_name)
            users_skipped += 1
            continue
        
        print(f"       ✓ Secret value retrieved from environment")
        print(f"       → Creating database and user...")
        
        try:
            # Create database if it doesn't exist
            print(f"         [SQL] CREATE DATABASE IF NOT EXISTS `{db_name}`")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")
            print(f"           ✓ Database created/exists")
            
            # Create user with proper escaping
            # Drop user if exists to avoid errors
            print(f"         [SQL] DROP USER IF EXISTS '{db_user_name}'@'%'")
            cursor.execute(f"DROP USER IF EXISTS '{db_user_name}'@'%';")
            print(f"         [SQL] DROP USER IF EXISTS '{db_user_name}'@'localhost'")
            cursor.execute(f"DROP USER IF EXISTS '{db_user_name}'@'localhost';")
            
            # Create user with all hosts
            create_user_sql = f"CREATE USER '{db_user_name}'@'%' IDENTIFIED BY <password>"
            print(f"         [SQL] {create_user_sql}")
            cursor.execute(f"CREATE USER '{db_user_name}'@'%' IDENTIFIED BY %s;", (db_user_pass,))
            print(f"           ✓ User created: {db_user_name}@'%'")
            
            # Grant all privileges on this database
            grant_sql = f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user_name}'@'%'"
            print(f"         [SQL] {grant_sql}")
            cursor.execute(grant_sql)
            print(f"           ✓ Privileges granted on {db_name}.*")
            
            # Flush privileges to apply changes
            print(f"         [SQL] FLUSH PRIVILEGES")
            cursor.execute("FLUSH PRIVILEGES;")
            print(f"           ✓ Privileges flushed")
            
            print(f"       ✅ SUCCESS: User setup complete\n")
            users_created += 1
            
        except mysql.connector.Error as e:
            print(f"       ❌ ERROR: Failed to setup user")
            print(f"          MySQL Error: {e}")
            print(f"          Database: {db_name}")
            print(f"          User: {db_user_name}\n")
            users_skipped += 1
            continue
    
    # Verify users were created
    print("[STEP 5] Verifying database users...")
    try:
        cursor.execute("SELECT User, Host FROM mysql.user WHERE User NOT IN ('mysql.sys', 'mysql.session', 'root');")
        users = cursor.fetchall()
        print(f"  Query successful - found {len(users)} total application users\n")
        
        print("\n" + "="*70)
        print("📊 DATABASE SETUP SUMMARY")
        print("="*70)
        print(f"✅ Users created successfully: {users_created}")
        print(f"↭️  Users skipped or failed: {users_skipped}")
        print(f"👥 Total application users in MySQL: {len(users)}")
        
        if missing_secrets:
            print(f"\n⚠️ MISSING SECRETS - Add these to GitHub Secrets:")
            for secret in missing_secrets:
                print(f"   - {secret}")
        else:
            print(f"\n✅ All required secrets are configured")
        
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"  [DEBUG] Could not verify users: {e}\n")
    
    cursor.close()
    connection.close()
    
    return 0 if users_created > 0 else 1


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 STARTING DATABASE USER SETUP SCRIPT")
    print("="*70)
    print(f"[INFO] Script: {sys.argv[0]}")
    print(f"[INFO] Python: {sys.version.split()[0]}")
    print()
    
    # Parse secrets array from command line argument
    available_secrets = []
    
    if len(sys.argv) > 1:
        try:
            secrets_arg = sys.argv[1]
            print(f"[DEBUG] Raw argument received (length {len(secrets_arg)} chars)")
            available_secrets = json.loads(secrets_arg)
            print(f"[DEBUG] Parsed {len(available_secrets)} secrets from JSON argument")
            print(f"[DEBUG] Secrets: {available_secrets}\n")
        except json.JSONDecodeError as e:
            print(f"❌ FAILED: Cannot parse secrets JSON argument")
            print(f"   Error: {e}")
            print(f"   Argument: {sys.argv[1]}\n")
            sys.exit(1)
    else:
        print("⚠️ WARNING: No secrets array provided as argument")
        print("   Script will process any schemas but skip those needing secrets\n")
    
    exit_code = setup_db_users(available_secrets)
    
    print("\n" + "="*70)
    if exit_code == 0:
        print("✅ SCRIPT COMPLETED SUCCESSFULLY")
    else:
        print("❌ SCRIPT FAILED WITH ERRORS")
    print("="*70 + "\n")
    
    sys.exit(exit_code)


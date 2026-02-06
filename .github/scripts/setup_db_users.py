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
    
    # Get configuration from environment
    base_dir = os.environ.get('BASE', '/opt/ecapps-hosting')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_user = os.environ.get('DB_ROOT_USER', 'root')
    db_pass = os.environ.get('DB_ROOT_PASS', '')
    
    schemas_dir = os.path.join(base_dir, 'data', 'schemas')
    
    print("👤 Setting up database users...\n")
    print(f"   📁 Looking for schemas in: {schemas_dir}")
    print(f"   🔐 Available secrets: {', '.join(available_secrets)}\n")
    
    # Check if schemas directory exists
    if not os.path.isdir(schemas_dir):
        print(f"   ⚠️ Schemas directory does not exist: {schemas_dir}")
        print("   ℹ️ This is OK if no databases have been synced yet")
        return 0
    
    # List what's in the schemas directory for debugging
    try:
        items = os.listdir(schemas_dir)
        print(f"   📋 Found {len(items)} item(s) in schemas directory")
        for item in items:
            item_path = os.path.join(schemas_dir, item)
            if os.path.isdir(item_path):
                print(f"      📁 {item}/")
            else:
                print(f"      📄 {item}")
    except Exception as e:
        print(f"   ⚠️ Could not list schemas directory: {e}")
    
    try:
        # Connect to MySQL as root
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            autocommit=True
        )
        cursor = connection.cursor()
        print(f"✅ Connected to MySQL at {db_host}\n")
        
    except mysql.connector.Error as e:
        print(f"❌ Failed to connect to MySQL: {e}")
        return 1
    
    users_created = 0
    users_skipped = 0
    missing_secrets = []
    
    # Iterate through each database directory
    for db_dir in sorted(os.listdir(schemas_dir)):
        db_path = os.path.join(schemas_dir, db_dir)
        config_file = os.path.join(db_path, 'db-config.json')
        
        # Skip if not a directory or no config file
        if not os.path.isdir(db_path):
            print(f"   ⏭️  Skipping (not a directory): {db_dir}")
            continue
            
        if not os.path.isfile(config_file):
            print(f"   ⏭️  No db-config.json in {db_dir}/")
            continue
        
        # Read config
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"   ⚠️ Could not read config for {db_dir}: {e}")
            users_skipped += 1
            continue
        
        db_name = config.get('database_name')
        db_user_name = config.get('database_user')
        secret_name = config.get('secret_name')
        
        print(f"   📋 Found config: {db_dir}")
        print(f"      - Database: {db_name}")
        print(f"      - User: {db_user_name}")
        print(f"      - Secret: {secret_name}")
        
        if not db_name or not db_user_name or not secret_name:
            print(f"   ⚠️ Incomplete config for {db_dir} - missing database_name, database_user, or secret_name")
            users_skipped += 1
            continue
        
        # Check if secret is in available list
        if secret_name not in available_secrets:
            print(f"      ❌ Secret '{secret_name}' not in available secrets list")
            missing_secrets.append(secret_name)
            users_skipped += 1
            continue
        
        # Get password from environment variable
        db_user_pass = os.environ.get(secret_name)
        
        if not db_user_pass:
            print(f"      ❌ Secret '{secret_name}' not found in environment")
            missing_secrets.append(secret_name)
            users_skipped += 1
            continue
        
        print(f"      ✅ Secret found")
        print(f"   📋 Processing: {db_name}")
        
        try:
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")
            print(f"      ✓ Database: {db_name}")
            
            # Create user with proper escaping
            # Drop user if exists to avoid errors
            cursor.execute(f"DROP USER IF EXISTS '{db_user_name}'@'%';")
            cursor.execute(f"DROP USER IF EXISTS '{db_user_name}'@'localhost';")
            
            # Create user with all hosts
            create_user_sql = f"CREATE USER '{db_user_name}'@'%' IDENTIFIED BY %s;"
            cursor.execute(create_user_sql, (db_user_pass,))
            print(f"      ✓ User created: {db_user_name}@'%'")
            
            # Grant all privileges on this database
            grant_sql = f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user_name}'@'%';"
            cursor.execute(grant_sql)
            print(f"      ✓ Permissions granted on {db_name}")
            
            # Flush privileges to apply changes
            cursor.execute("FLUSH PRIVILEGES;")
            
            print(f"   ✅ User setup complete for {db_name}\n")
            users_created += 1
            
        except mysql.connector.Error as e:
            print(f"   ❌ Error setting up user for {db_name}: {e}\n")
            users_skipped += 1
            continue
    
    # Verify users were created
    try:
        cursor.execute("SELECT User, Host FROM mysql.user WHERE User NOT IN ('mysql.sys', 'mysql.session', 'root');")
        users = cursor.fetchall()
        print(f"\n📊 Summary:")
        print(f"   ✅ Users created: {users_created}")
        print(f"   ⏭️  Users skipped/failed: {users_skipped}")
        print(f"   📝 Total application users in MySQL: {len(users)}\n")
        
        if missing_secrets:
            print(f"⚠️ Missing secrets (add these to GitHub Secrets):")
            for secret in missing_secrets:
                print(f"   - {secret}")
    except Exception as e:
        print(f"⚠️ Could not verify users: {e}\n")
    
    cursor.close()
    connection.close()
    
    return 0 if users_created > 0 else 1


if __name__ == '__main__':
    # Parse secrets array from command line argument
    available_secrets = []
    
    if len(sys.argv) > 1:
        try:
            available_secrets = json.loads(sys.argv[1])
            print(f"📌 Received {len(available_secrets)} secrets from workflow\n")
        except json.JSONDecodeError:
            print(f"❌ Failed to parse secrets JSON: {sys.argv[1]}")
            sys.exit(1)
    else:
        print("⚠️ No secrets array provided as argument")
    
    sys.exit(setup_db_users(available_secrets))


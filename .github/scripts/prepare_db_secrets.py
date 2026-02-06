#!/usr/bin/env python3
"""
Setup database users by reading secret names from db-config.json
and looking them up from environment variables
"""

import sys
import os
import subprocess
import json

def get_all_env_vars_starting_with(prefix):
    """Get all environment variables starting with prefix"""
    return {k: v for k, v in os.environ.items() if k.startswith(prefix)}

def extract_secret_names_from_configs(schemas_dir):
    """Extract all secret names from db-config.json files"""
    secret_names = set()
    
    if not os.path.isdir(schemas_dir):
        return secret_names
    
    for db_dir in os.listdir(schemas_dir):
        db_path = os.path.join(schemas_dir, db_dir)
        config_file = os.path.join(db_path, 'db-config.json')
        
        if os.path.isfile(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    secret_name = config.get('secret_name')
                    if secret_name:
                        secret_names.add(secret_name)
            except Exception:
                pass
    
    return secret_names

def inject_secrets_into_env(schemas_dir):
    """
    Read all required secret names from configs,
    then prepare them as environment variables for the SSH session
    """
    
    secret_names = extract_secret_names_from_configs(schemas_dir)
    available_env_vars = get_all_env_vars_starting_with('DB_')
    
    print("🔍 Environment Variable Scan:")
    print(f"   Required secrets from configs: {', '.join(sorted(secret_names)) or 'None'}")
    print(f"   Available DB_* env vars: {', '.join(sorted(available_env_vars.keys())) or 'None'}\n")
    
    missing = secret_names - set(available_env_vars.keys())
    if missing:
        print(f"⚠️  Missing environment variables (add to GitHub Secrets):")
        for secret in sorted(missing):
            print(f"   - {secret}")
        print()
    
    found = secret_names & set(available_env_vars.keys())
    if found:
        print(f"✅ Found environment variables:")
        for secret in sorted(found):
            print(f"   - {secret}")
        print()
    
    return available_env_vars

def main():
    base_dir = os.environ.get('BASE', '/opt/ecapps-hosting')
    schemas_dir = os.path.join(base_dir, 'data', 'schemas')
    
    print("🔐 Preparing database secrets from environment...\n")
    
    # Get all available DB_* secrets
    env_vars = inject_secrets_into_env(schemas_dir)
    
    # Export them so they're available to child processes
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("\n✅ All available secrets prepared for Python script\n")
    
    # Now call the actual setup script
    setup_script = os.path.join(base_dir, '.github/scripts/setup_db_users.py')
    
    if not os.path.isfile(setup_script):
        print(f"❌ Setup script not found: {setup_script}")
        return 1
    
    # Run the setup script with all env vars available
    result = subprocess.run([sys.executable, setup_script], env=os.environ.copy())
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())

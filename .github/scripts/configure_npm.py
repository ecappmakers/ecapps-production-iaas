import os
import json
import requests
import sys
import time
import urllib3

# Suppress SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
NPM_BASE_URL = os.environ.get("NPM_BASE_URL", "https://localhost:81")
APPS_FILE = os.environ.get("APPS_FILE", "apps.json")
NPM_TIMEOUT = int(os.environ.get("NPM_TIMEOUT", "90"))

NPM_USER = os.environ.get("NPM_USER")
NPM_PASS = os.environ.get("NPM_PASS")

if not NPM_USER or not NPM_PASS:
    print("❌ Error: NPM_USER and NPM_PASS environment variables are required.")
    sys.exit(1)

def get_token():
    """Login and retrieve a Bearer Token with retries"""
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            url = f"{NPM_BASE_URL}/api/tokens"
            payload = {"identity": NPM_USER, "secret": NPM_PASS}
            response = requests.post(url, json=payload, timeout=15, verify=False)
            response.raise_for_status()
            return response.json()['token']
        except requests.exceptions.Timeout:
            wait_time = min(2 ** attempt, 10)
            print(f"⏳ Login timeout (attempt {attempt+1}/{max_attempts}), retrying in {wait_time}s...")
            time.sleep(wait_time)
        except requests.exceptions.ConnectionError as e:
            wait_time = min(2 ** attempt, 10)
            print(f"⏳ Connection error (attempt {attempt+1}/{max_attempts}), retrying in {wait_time}s...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"❌ Login Failed: {e}")
            sys.exit(1)
    
    print("❌ Could not authenticate after all retries")
    sys.exit(1)

def get_existing_hosts(token):
    """Fetch list of already configured domains with retries"""
    headers = {"Authorization": f"Bearer {token}"}
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{NPM_BASE_URL}/api/nginx/proxy-hosts", headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            existing = set()
            for host in response.json():
                for name in host['domain_names']:
                    existing.add(name)
            return existing
        except requests.exceptions.Timeout:
            wait_time = min(2 ** attempt, 10)
            print(f"⏳ Fetching hosts timeout (attempt {attempt+1}/{max_attempts}), retrying in {wait_time}s...")
            time.sleep(wait_time)
        except requests.exceptions.ConnectionError:
            wait_time = min(2 ** attempt, 10)
            print(f"⏳ Connection error fetching hosts, retrying in {wait_time}s...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"❌ Failed to fetch existing hosts: {e}")
            return set()
    
    print("⚠️  Could not fetch existing hosts, proceeding without check")
    return set()

def create_proxy_host(token, app):
    """Create a new Proxy Host with Auto-SSL and retry logic"""
    headers = {"Authorization": f"Bearer {token}"}
    domain = app.get('domain')
    
    # Routing Logic
    if app.get('type') == 'container':
        forward_host = app.get('name')
        forward_port = app.get('port', 80)
    else:
        # Route static sites to the shared Apache container
        forward_host = "shared_web"
        forward_port = 80

    payload = {
        "domain_names": [domain, f"www.{domain}"],
        "forward_scheme": "http",
        "forward_host": forward_host,
        "forward_port": int(forward_port),
        "access_list_id": 0,
        "certificate_id": "new",
        "ssl_forced": True,
        "meta": {
            "letsencrypt_email": NPM_USER,
            "letsencrypt_agree": True,
            "dns_challenge": False
        },
        "block_exploits": True,
        "caching_enabled": True,
        "allow_websocket_upgrade": True,
        "http2_support": True
    }

    print(f"⚙️  Configuring {domain} -> {forward_host}:{forward_port}")

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            response = requests.post(f"{NPM_BASE_URL}/api/nginx/proxy-hosts", headers=headers, json=payload, timeout=15, verify=False)
            if response.status_code == 201:
                print(f"✅ Created: {domain}")
                return True
            else:
                print(f"⚠️  Failed {domain} (Status: {response.status_code})")
                print(f"   Response: {response.text}")
                return False
        except requests.exceptions.Timeout:
            wait_time = min(2 ** attempt, 10)
            if attempt < max_attempts - 1:
                print(f"⏳ Request timeout for {domain}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ Could not configure {domain} after retries")
                return False
        except Exception as e:
            print(f"❌ API Error for {domain}: {e}")
            return False

def main():
    print("🚀 Starting Nginx Proxy Manager Auto-Configuration...")
    print(f"⏱️  Timeout configured: {NPM_TIMEOUT}s")
    
    if not os.path.exists(APPS_FILE):
        print("❌ apps.json not found!")
        sys.exit(1)
    
    with open(APPS_FILE, 'r') as f:
        config = json.load(f)
    
    # Authenticate
    print("🔐 Authenticating to NPM...")
    token = get_token()
    print("✅ Authenticated successfully.")
    
    # Fetch existing hosts
    print("📋 Fetching existing proxy hosts...")
    existing_domains = get_existing_hosts(token)
    print(f"📊 Found {len(existing_domains)} existing domain(s)")
    
    # Configure apps
    apps_to_config = [app for app in config.get('apps', []) if app.get('type') != 'migration' and app.get('domain')]
    if not apps_to_config:
        print("ℹ️  No applications to configure")
        return
    
    print(f"⚙️  Processing {len(apps_to_config)} application(s)...\n")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for app in apps_to_config:
        domain = app.get('domain')
        
        if domain in existing_domains:
            print(f"ℹ️  Skipping {domain} (Already Exists)")
            skip_count += 1
        else:
            if create_proxy_host(token, app):
                success_count += 1
            else:
                fail_count += 1
    
    # Summary
    print(f"\n📊 Configuration Summary:")
    print(f"   ✅ Created: {success_count}")
    print(f"   ℹ️  Skipped: {skip_count}")
    print(f"   ❌ Failed:  {fail_count}")
    
    if fail_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
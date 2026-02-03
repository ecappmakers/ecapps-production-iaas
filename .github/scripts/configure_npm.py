import os
import json
import requests
import sys
import time

# --- CONFIGURATION ---
NPM_BASE_URL = "https://pm.ecapps.in" # Ensure this matches your Admin Panel URL
APPS_FILE = "apps.json"

NPM_USER = os.environ.get("NPM_USER")
NPM_PASS = os.environ.get("NPM_PASS")

if not NPM_USER or not NPM_PASS:
    print("❌ Error: NPM_USER and NPM_PASS environment variables are required.")
    sys.exit(1)

def get_token():
    """Login and retrieve a Bearer Token"""
    try:
        url = f"{NPM_BASE_URL}/api/tokens"
        payload = {"identity": NPM_USER, "secret": NPM_PASS}
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()['token']
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        sys.exit(1)

def get_existing_hosts(token):
    """Fetch list of already configured domains"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{NPM_BASE_URL}/api/nginx/proxy-hosts", headers=headers, timeout=10)
        response.raise_for_status()
        existing = set()
        for host in response.json():
            for name in host['domain_names']:
                existing.add(name)
        return existing
    except Exception as e:
        print(f"❌ Failed to fetch existing hosts: {e}")
        sys.exit(1)

def create_proxy_host(token, app):
    """Create a new Proxy Host with Auto-SSL"""
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
        "certificate_id": "new", # Auto-Request Let's Encrypt
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

    try:
        response = requests.post(f"{NPM_BASE_URL}/api/nginx/proxy-hosts", headers=headers, json=payload)
        if response.status_code == 201:
            print(f"✅ Created: {domain}")
        else:
            print(f"⚠️  Failed {domain} (Status: {response.status_code})")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ API Error: {e}")

def main():
    print("🚀 Starting Nginx Proxy Manager Auto-Configuration...")
    
    if not os.path.exists(APPS_FILE):
        print("❌ apps.json not found!")
        sys.exit(1)
    
    with open(APPS_FILE, 'r') as f:
        config = json.load(f)
    
    # Retry logic for login (in case NPM container is waking up)
    token = None
    for attempt in range(3):
        try:
            token = get_token()
            print("🔑 Authenticated successfully.")
            break
        except:
            print(f"⏳ NPM not ready, retrying ({attempt+1}/3)...")
            time.sleep(5)
    
    if not token:
        print("❌ Could not connect to NPM after retries.")
        sys.exit(1)

    existing_domains = get_existing_hosts(token)
    
    for app in config.get('apps', []):
        if app.get('type') == 'migration': continue
        
        domain = app.get('domain')
        if not domain: continue

        if domain in existing_domains:
            print(f"ℹ️  Skipping {domain} (Already Exists)")
        else:
            create_proxy_host(token, app)

if __name__ == "__main__":
    main()
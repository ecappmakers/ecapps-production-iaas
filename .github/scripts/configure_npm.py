import os
import json
import requests
import sys
import time
import urllib3

# Suppress SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
NPM_BASE_URL = os.environ.get("NPM_BASE_URL", "https://pm.ecapps.in")
APPS_FILE = os.environ.get("APPS_FILE", "apps.json")
NPM_TIMEOUT = int(os.environ.get("NPM_TIMEOUT", "120"))

NPM_USER = os.environ.get("NPM_USER")
NPM_PASS = os.environ.get("NPM_PASS")

if not NPM_USER or not NPM_PASS:
    print("❌ Error: NPM_USER and NPM_PASS environment variables are required.")
    print(f"   NPM_USER: {'SET' if NPM_USER else 'NOT SET'}")
    print(f"   NPM_PASS: {'SET' if NPM_PASS else 'NOT SET'}")
    sys.exit(1)

def check_npm_health():
    """Check if NPM API is healthy and ready"""
    print("🩺 Checking NPM health...")
    max_wait = 120
    wait_time = 0
    
    while wait_time < max_wait:
        try:
            response = requests.get(f"{NPM_BASE_URL}/api/settings", timeout=10, verify=False)
            status_code = response.status_code
            
            # Any 4xx or 5xx indicates the API is responding
            if status_code in [200, 401, 403, 404, 500]:
                print(f"✅ NPM API is healthy (HTTP {status_code})")
                return True
            else:
                print(f"   HTTP {status_code} - Waiting... ({max_wait - wait_time}s remaining)")
        except requests.exceptions.Timeout:
            print(f"   Timeout - Waiting for NPM... ({max_wait - wait_time}s remaining)")
        except requests.exceptions.ConnectionError:
            print(f"   Connection refused - NPM warming up... ({max_wait - wait_time}s remaining)")
        except Exception as e:
            print(f"   Error: {e} - Retrying... ({max_wait - wait_time}s remaining)")
        
        time.sleep(3)
        wait_time += 3
    
    print("⚠️  NPM health check timeout, but proceeding with configuration...")
    return False

def get_token():
    """Login and retrieve a Bearer Token with retries"""
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            url = f"{NPM_BASE_URL}/api/tokens"
            # Try without expiry first (some NPM versions don't support it)
            payload = {
                "identity": NPM_USER,
                "secret": NPM_PASS
            }
            print(f"🔐 Attempt {attempt+1}/{max_attempts}: Connecting to {url}...")
            print(f"   Payload: identity=*****, secret=*****")
            
            response = requests.post(url, json=payload, timeout=15, verify=False)
            
            # Debug info
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 400:
                # Try with expiry parameter
                print(f"   Retrying with expiry parameter...")
                payload["expiry"] = "1y"
                response = requests.post(url, json=payload, timeout=15, verify=False)
                print(f"   Response Status (with expiry): {response.status_code}")
            
            response.raise_for_status()
            token = response.json().get('token')
            if not token:
                raise ValueError("No token in response")
            print(f"✅ Authentication successful (Token obtained)")
            return token
        except requests.exceptions.Timeout:
            wait_time = min(2 ** attempt, 10)
            print(f"⏳ Request timeout (attempt {attempt+1}/{max_attempts}), retrying in {wait_time}s...")
            time.sleep(wait_time)
        except requests.exceptions.ConnectionError as e:
            wait_time = min(2 ** attempt, 10)
            print(f"⏳ Connection refused (attempt {attempt+1}/{max_attempts}): {e}")
            print(f"   Retrying in {wait_time}s...")
            time.sleep(wait_time)
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"   Response: {response.text}")
            if response.status_code == 400:
                print(f"   Credentials may be incorrect or API format differs")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Login Failed: {e}")
            sys.exit(1)
    
    print("❌ Could not authenticate after all retries")
    sys.exit(1)

def get_existing_hosts(token):
    """Fetch list of already configured domains with retries"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
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
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
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
            elif response.status_code == 401:
                print(f"❌ Authentication failed (401): Invalid token or credentials")
                print(f"   Response: {response.text}")
                return False
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
    print(f"📍 NPM URL: {NPM_BASE_URL}")
    print(f"⏱️  Timeout configured: {NPM_TIMEOUT}s")
    print(f"📄 Apps file: {APPS_FILE}\n")
    
    # Step 1: Health check
    print("=" * 50)
    check_npm_health()
    print("=" * 50)
    print()
    
    # Verify NPM is reachable
    print("🔗 Testing NPM connectivity...")
    try:
        response = requests.get(f"{NPM_BASE_URL}/api/settings", timeout=10, verify=False)
        print(f"   NPM is reachable (HTTP {response.status_code})")
    except Exception as e:
        print(f"⚠️  Cannot reach NPM: {e}")
        print(f"   Continuing anyway, authentication may fail...")
    
    print()
    
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
import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime

def log(message):
    """Simple logger to print to stdout with timestamp."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def send_telegram_notification():
    log("🚀 Starting Telegram notification script...")

    # 1. Retrieve Environment Variables
    bot_token = os.environ.get("BOT_TOKEN")
    chat_id = os.environ.get("CHAT_ID")
    repo = os.environ.get("REPO", "Unknown Repository")
    size = os.environ.get("BACKUP_SIZE", "0B")
    job_status = os.environ.get("JOB_STATUS", "unknown").lower()
    history = os.environ.get("HISTORICAL_TEXT", "No historical data available.")

    # Validate critical secrets
    if not bot_token or not chat_id:
        log("❌ Error: Missing BOT_TOKEN or CHAT_ID environment variables.")
        sys.exit(1)

    # 2. Determine Icons and Headers based on Status
    if job_status == "success":
        status_icon = "✅"
        header_text = "SYSTEM INTEGRITY VERIFIED"
        status_text = "BACKUP OPERATION SUCCESSFUL"
    else:
        status_icon = "❌"
        header_text = "SYSTEM ALERT: OPERATION FAILED"
        status_text = "BACKUP OPERATION ENCOUNTERED ERRORS"

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')

    # 3. Construct the "Exaggerated" HTML Message
    # We use <pre> for the history to ensure monospaced alignment on mobile
    message_html = (
        f"<b>{status_icon} {header_text}</b>\n"
        f"─────────────────────────────\n"
        f"<b>🛡️ TARGET IDENTITY:</b> {repo}\n"
        f"<b>⚙️ OPERATIONAL STATUS:</b> {status_text}\n"
        f"<b>📦 ARCHIVE PAYLOAD:</b> {size}\n"
        f"<b>🕒 EXECUTION TIMESTAMP:</b> {current_time}\n"
        f"─────────────────────────────\n"
        f"<b>📜 ARCHIVAL MANIFEST (LAST 5):</b>\n"
        f"<pre>{history}</pre>\n"
        f"─────────────────────────────\n"
        f"<i>🤖 Automated Security Protocol via GitHub Actions</i>"
    )

    log("📝 Message payload constructed successfully.")

    # 4. Send Request to Telegram API
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": message_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        log(f"📡 Sending request to {api_url}...")
        
        # Encoding data
        data_encoded = json.dumps(data).encode('utf-8')
        
        # Creating request
        req = urllib.request.Request(
            api_url, 
            data=data_encoded, 
            headers={'Content-Type': 'application/json'}
        )
        
        # Executing request
        with urllib.request.urlopen(req) as response:
            response_body = response.read().decode('utf-8')
            log(f"✅ Notification sent successfully. API Response: {response.status}")
            
    except urllib.error.HTTPError as e:
        log(f"❌ HTTP Error: {e.code} - {e.reason}")
        log(f"Response: {e.read().decode('utf-8')}")
        sys.exit(1)
    except urllib.error.URLError as e:
        log(f"❌ URL Error: {e.reason}")
        sys.exit(1)
    except Exception as e:
        log(f"❌ Unexpected Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    send_telegram_notification()
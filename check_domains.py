import whois
import requests
import datetime
import os

# --- Settings ---

# 1. Domains loaded from GitHub Secret 'DOMAINS_LIST'
DOMAINS_SECRET = os.environ.get("DOMAINS_LIST")

# 2. Notification schedule (days before expiration)
# A. Notify on these specific days
NOTIFY_SPECIFIC_DAYS = [60, 45, 30, 15]

# B. Start sending daily notifications this many days before expiry
# (Setting this to 7 means you get alerts on 7, 6, 5, 4, 3, 2, 1, and 0)
NOTIFY_DAILY_BEFORE_DAYS = 7

# 3. Notification Service Secrets (from GitHub Secrets)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# --- Main Script ---

def get_domains_from_secret(secret_data):
    """Reads domains from the multi-line secret string."""
    if not secret_data:
        print("ERROR: DOMAINS_LIST secret is not set.")
        return []
    
    domains = []
    for line in secret_data.splitlines():
        line = line.strip()
        # Ignore empty lines and comments
        if line and not line.startswith('#'):
            domains.append(line)
            
    print(f"Successfully loaded {len(domains)} domains from secret.")
    return domains

# --- Notification Functions ---

def send_telegram_message(message):
    """Sends a message via Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # Escape special chars for Telegram MarkdownV2
    safe_message = message.replace('.', r'\.').replace('-', r'\-').replace('(', r'\(').replace(')', r'\)').replace('!', r'\!')
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': safe_message, 'parse_mode': 'MarkdownV2'}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Telegram message sent successfully.")
        else:
            print(f"Failed to send Telegram message: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def send_discord_webhook(message):
    """Sends a message via Discord Webhook."""
    try:
        payload = {"content": message}
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        print("Discord message sent successfully.")
    except Exception as e:
        print(f"Failed to send Discord message: {e}")

def send_slack_webhook(message):
    """Sends a message via Slack Webhook."""
    try:
        # Slack uses *bold* instead of **bold**
        safe_message = message.replace('**', '*')
        payload = {"text": safe_message}
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        print("Slack message sent successfully.")
    except Exception as e:
        print(f"Failed to send Slack message: {e}")

def send_notification(message):
    """Checks ALL configured notification services and sends alerts to each one."""
    service_configured = False 

    # --- Check for Telegram ---
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("Telegram service configured. Sending message...")
        send_telegram_message(message)
        service_configured = True
        
    # --- Check for Discord ---
    if DISCORD_WEBHOOK_URL:
        print("Discord service configured. Sending message...")
        send_discord_webhook(message)
        service_configured = True
        
    # --- Check for Slack ---
    if SLACK_WEBHOOK_URL:
        print("Slack service configured. Sending message...")
        send_slack_webhook(message)
        service_configured = True
        
    # --- If no services are configured ---
    if not service_configured:
        print("No notification service is configured (Telegram, Discord, or Slack).")

# --- Domain Checking Logic ---

def check_domains(domains_to_check):
    """Checks domain expiration."""
    # Use offset-aware UTC time for correct subtraction
    today = datetime.datetime.now(datetime.timezone.utc)
    alerts = []

    print(f"Today's date: {today.date()}. Starting domain check...")

    if not domains_to_check:
        print("No domains to check. Exiting.")
        return

    for domain_name in domains_to_check:
        print(f"--- Checking: {domain_name} ---") # Added for clarity
        try:
            w = whois.whois(domain_name)
            expiry_date = w.expiration_date
            if isinstance(expiry_date, list):
                expiry_date = expiry_date[0] # Take the first date if it's a list

            if expiry_date:
                # Ensure expiry_date is also offset-aware (assume UTC if naive)
                if expiry_date.tzinfo is None:
                    expiry_date = expiry_date.replace(tzinfo=datetime.timezone.utc)
                
                time_left = expiry_date - today
                days_left = time_left.days
                
                print(f"  [WHOIS] Days left: {days_left} (Expires on: {expiry_date.date()})")

                # --- Notification Logic ---
                # A. Check if it's a specific day
                should_notify = (days_left in NOTIFY_SPECIFIC_DAYS)
                
                # B. Check if it's in the daily notification range
                if not should_notify:
                    if 0 <= days_left <= NOTIFY_DAILY_BEFORE_DAYS:
                        should_notify = True
                # --- ------------------- ---

                if should_notify:
                    alert_message = (
                        f"🚨 **Domain Alert** 🚨\n"
                        f"`{domain_name}` will expire in **{days_left}** days!\n"
                        f"(Expiration Date: {expiry_date.date()})"
                    )
                    alerts.append(alert_message)
                
            else:
                print(f"  [WHOIS] Expiration date not found.")

        except Exception as e:
            print(f"  [WHOIS] Error checking: {e}")
            # We don't append a user-facing error for temporary network issues
            # alerts.append(f"❌ Could not check WHOIS for `{domain_name}`. Error: {e}")

    if alerts:
        final_message = "\n\n".join(alerts)
        send_notification(final_message)
    else:
        print("All domains are fine. No alerts.")

if __name__ == "__main__":
    domains = get_domains_from_secret(DOMAINS_SECRET)
    check_domains(domains)
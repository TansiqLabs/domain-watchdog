import whois
import requests
import datetime
import os
import ssl
import socket

# --- Settings ---

# 1. Domains will be loaded from this file
DOMAIN_FILE = "domains.txt"

# 2. WHOIS Notification schedule
NOTIFY_WHOIS_SPECIFIC_DAYS = [60, 45, 30, 15]
NOTIFY_WHOIS_DAILY_BEFORE_DAYS = 10 # 10 দিন আগে থেকে প্রতিদিন

# 3. SSL Notification schedule
NOTIFY_SSL_SPECIFIC_DAYS = [30, 15, 7]
NOTIFY_SSL_DAILY_BEFORE_DAYS = 3  # 3 দিন আগে থেকে প্রতিদিন

# 4. Notification Service Secrets
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# --- Main Script ---

def get_domains_from_file(filename):
    """Reads a list of domains from a text file."""
    domains = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Ignore empty lines and comments
                if line and not line.startswith('#'):
                    domains.append(line)
        print(f"Successfully loaded {len(domains)} domains from {filename}.")
    except FileNotFoundError:
        print(f"ERROR: Domain file '{filename}' not found.")
    except Exception as e:
        print(f"ERROR: Could not read domain file: {e}")
    return domains

# --- Notification Functions (No changes needed) ---

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    safe_message = message.replace('.', r'\.').replace('-', r'\-').replace('(', r'\(').replace(')', r'\)').replace('!', r'\!')
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': safe_message, 'parse_mode': 'MarkdownV2'}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200: print("Telegram message sent successfully.")
        else: print(f"Failed to send Telegram message: {response.status_code} - {response.text}")
    except Exception as e: print(f"Failed to send Telegram message: {e}")

def send_discord_webhook(message):
    try:
        payload = {"content": message}
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
        print("Discord message sent successfully.")
    except Exception as e: print(f"Failed to send Discord message: {e}")

def send_slack_webhook(message):
    try:
        safe_message = message.replace('**', '*')
        payload = {"text": safe_message}
        requests.post(SLACK_WEBHOOK_URL, json=payload)
        print("Slack message sent successfully.")
    except Exception as e: print(f"Failed to send Slack message: {e}")

def send_notification(message):
    service_configured = False
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("Telegram service configured. Sending message...")
        send_telegram_message(message)
        service_configured = True
    if DISCORD_WEBHOOK_URL:
        print("Discord service configured. Sending message...")
        send_discord_webhook(message)
        service_configured = True
    if SLACK_WEBHOOK_URL:
        print("Slack service configured. Sending message...")
        send_slack_webhook(message)
        service_configured = True
    if not service_configured:
        print("No notification service is configured.")

# --- Expiry Check Functions (No changes needed) ---

def check_whois_expiry(domain_name, today_utc):
    """Checks WHOIS (Domain) expiration."""
    try:
        w = whois.whois(domain_name)
        expiry_date = w.expiration_date
        if isinstance(expiry_date, list): expiry_date = expiry_date[0]

        if expiry_date:
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=datetime.timezone.utc)
            
            time_left = expiry_date - today_utc
            days_left = time_left.days
            
            print(f"  [WHOIS] Days left: {days_left} (Expires on: {expiry_date.date()})")

            should_notify = (days_left in NOTIFY_WHOIS_SPECIFIC_DAYS)
            if not should_notify:
                if 0 <= days_left <= NOTIFY_WHOIS_DAILY_BEFORE_DAYS:
                    should_notify = True
            
            if should_notify:
                return (
                    f"🚨 **Domain Alert** 🚨\n"
                    f"`{domain_name}` will expire in **{days_left}** days!\n"
                    f"(Expiration Date: {expiry_date.date()})"
                )
        else:
            print(f"  [WHOIS] Expiration date not found.")
    except Exception as e:
        print(f"  [WHOIS] Error checking: {e}")
        return f"❌ Could not check WHOIS for `{domain_name}`. Error: {e}"
    return None

def check_ssl_expiry(domain_name, today_utc):
    """Checks SSL Certificate expiration."""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain_name, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain_name) as sslsock:
                cert = sslsock.getpeercert()
                expiry_date_str = cert['notAfter']
                expiry_date = datetime.datetime.strptime(expiry_date_str, "%b %d %H:%M:%S %Y %Z")
                expiry_date = expiry_date.replace(tzinfo=datetime.timezone.utc)
                
                time_left = expiry_date - today_utc
                days_left = time_left.days

                print(f"  [SSL] Days left: {days_left} (Expires on: {expiry_date.date()})")
                
                should_notify = (days_left in NOTIFY_SSL_SPECIFIC_DAYS)
                if not should_notify:
                    if 0 <= days_left <= NOTIFY_SSL_DAILY_BEFORE_DAYS:
                        should_notify = True
                
                if should_notify:
                    return (
                        f"🛡️ **SSL Alert** 🛡️\n"
                        f"`{domain_name}` SSL certificate will expire in **{days_left}** days!\n"
                        f"(Expiration Date: {expiry_date.date()})"
                    )
    except socket.timeout:
        print(f"  [SSL] Timeout checking {domain_name} (Port 443).")
        return f"❌ SSL check for `{domain_name}` timed out. (Port 443 closed?)"
    except (ssl.SSLError, socket.gaierror) as e:
        print(f"  [SSL] Error checking {domain_name}: {e}")
        return f"❌ SSL check for `{domain_name}` failed. (No SSL certificate?)"
    except Exception as e:
        print(f"  [SSL] Unknown error checking {domain_name}: {e}")
        return f"❌ Unknown SSL error for `{domain_name}`: {e}"
    return None

# --- Main Domain Loop ---

def check_all_domains(domains_to_check):
    """Runs all checks for all domains."""
    today_utc = datetime.datetime.now(datetime.timezone.utc)
    alerts = []
    print(f"Today's date: {today_utc.date()}. Starting all checks...")

    if not domains_to_check:
        print("No domains to check. Exiting.")
        return

    for domain_name in domains_to_check:
        print(f"--- Checking: {domain_name} ---")
        
        # Check #1: WHOIS (Domain) Expiry
        whois_alert = check_whois_expiry(domain_name, today_utc)
        if whois_alert:
            alerts.append(whois_alert)
        
        # Check #2: SSL Certificate Expiry
        ssl_alert = check_ssl_expiry(domain_name, today_utc)
        if ssl_alert:
            alerts.append(ssl_alert)

    if alerts:
        final_message = "\n\n".join(alerts)
        send_notification(final_message)
    else:
        print("All domains and SSL certs are fine. No alerts.")

if __name__ == "__main__":
    domains = get_domains_from_file(DOMAIN_FILE)
    check_all_domains(domains)
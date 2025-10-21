import whois
import requests
import datetime
import os

# --- Settings ---

# The script now reads domains from 'domains.txt'
DOMAIN_FILE = "domains.txt" 

# 1. Notification schedule (days before expiration)
NOTIFY_DAYS = [60, 45, 30, 15, 7, 6, 5, 4, 3, 2, 1, 0]

# 2. Webhook URL (from GitHub Secrets)
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

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

def send_webhook(message):
    """Sends a message to the webhook."""
    if not WEBHOOK_URL:
        print("WEBHOOK_URL not found. Is the GitHub Secret set?")
        return
    try:
        # 'content' for Discord, 'text' for Slack
        payload = {"content": message} 
        requests.post(WEBHOOK_URL, json=payload)
        print(f"Webhook sent: {message}")
    except Exception as e:
        print(f"Failed to send webhook: {e}")

def check_domains(domains_to_check):
    """Checks domain expiration."""
    
    # FIX: Use offset-aware UTC time for 'today'
    today = datetime.datetime.now(datetime.timezone.utc)
    
    alerts = [] # All alerts will be collected here

    print(f"Today's date: {today.date()}. Starting domain check...")

    if not domains_to_check:
        print("No domains to check. Exiting.")
        return

    for domain_name in domains_to_check:
        try:
            w = whois.whois(domain_name)
            
            expiry_date = w.expiration_date
            if isinstance(expiry_date, list):
                expiry_date = expiry_date[0] # Take the first date if it's a list

            if expiry_date:
                # If expiry_date is naive, assume it's UTC (this is rare but safe)
                if expiry_date.tzinfo is None:
                    expiry_date = expiry_date.replace(tzinfo=datetime.timezone.utc)
                
                time_left = expiry_date - today
                days_left = time_left.days
                
                print(f"Domain: {domain_name}, Days left: {days_left} (Expires on: {expiry_date.date()})")

                if days_left in NOTIFY_DAYS:
                    alert_message = (
                        f"🚨 **Domain Alert** 🚨\n"
                        f"`{domain_name}` will expire in **{days_left}** days!\n"
                        f"(Expiration Date: {expiry_date.date()})"
                    )
                    alerts.append(alert_message)
                
            else:
                print(f"Expiration date not found for '{domain_name}'.")

        except Exception as e:
            print(f"Error checking '{domain_name}': {e}")
            alerts.append(f"❌ Could not check `{domain_name}`. Error: {e}")

    # Send a single webhook if there are any alerts
    if alerts:
        final_message = "\n\n".join(alerts)
        send_webhook(final_message)
    else:
        print("All domains are fine. No alerts.")

if __name__ == "__main__":
    domains = get_domains_from_file(DOMAIN_FILE)
    check_domains(domains)
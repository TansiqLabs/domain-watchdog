import whois
import requests
import datetime
import os

DOMAINS_TO_CHECK = [
    "tansiqlabs.com",
    "tansiqlabs.dev"
]

NOTIFY_DAYS = [60, 45, 30, 15, 7, 6, 5, 4, 3, 2, 1, 0]

# ৩. ওয়েবহুক ইউআরএল (GitHub Secrets থেকে আসবে)
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# --- মূল স্ক্রিপ্ট ---
    
def send_webhook(message):
    """ওয়েবহুকে মেসেজ পাঠায়"""
    if not WEBHOOK_URL:
        print("WEBHOOK_URL পাওয়া যায়নি। GitHub Secret সেট করা আছে কি?")
        return
    try:
        payload = {"content": message} # Discord-এর জন্য 'content', Slack-এর জন্য 'text'
        requests.post(WEBHOOK_URL, json=payload)
        print(f"ওয়েবহুক পাঠানো হয়েছে: {message}")
    except Exception as e:
        print(f"ওয়েবহুক পাঠাতে সমস্যা হয়েছে: {e}")

def check_domains():
    """ডোমেইনের মেয়াদ চেক করে"""
    today = datetime.datetime.now()
    alerts = [] # সব অ্যালার্ট এখানে জমা হবে

    print(f"আজকের তারিখ: {today.date()}. ডোমেইন চেক শুরু...")

    for domain_name in DOMAINS_TO_CHECK:
        try:
            w = whois.whois(domain_name)
            
            # WHOIS লাইব্রেরি কখনো একটি ডেট, কখনো লিস্ট পাঠায়
            expiry_date = w.expiration_date
            if isinstance(expiry_date, list):
                expiry_date = expiry_date[0] # তালিকার প্রথমটি নিচ্ছি

            if expiry_date:
                time_left = expiry_date - today
                days_left = time_left.days
                
                print(f"ডোমেইন: {domain_name}, মেয়াদ আছে: {days_left} দিন (তারিখ: {expiry_date.date()})")

                # আপনার নির্দিষ্ট অ্যালার্ট শিডিউল চেক করা হচ্ছে
                if days_left in NOTIFY_DAYS:
                    alert_message = f"🚨 **ডোমেইন অ্যালার্ট** 🚨\n`{domain_name}`-এর মেয়াদ **{days_left}** দিনের মধ্যে শেষ হবে!\n(মেয়াদ শেষ হওয়ার তারিখ: {expiry_date.date()})"
                    alerts.append(alert_message)
                
            else:
                print(f"'{domain_name}'-এর মেয়াদ শেষ হওয়ার তারিখ পাওয়া যায়নি।")

        except Exception as e:
            print(f"'{domain_name}' চেক করতে সমস্যা হয়েছে: {e}")
            alerts.append(f"❌ `{domain_name}` চেক করা সম্ভব হয়নি। Error: {e}")

    # যদি কোনো অ্যালার্ট থাকে, তবে একটিমাত্র ওয়েবহুক পাঠানো হবে
    if alerts:
        final_message = "\n\n".join(alerts)
        send_webhook(final_message)
    else:
        print("সব ডোমেইনের মেয়াদ ঠিক আছে। কোনো অ্যালার্ট নেই।")

if __name__ == "__main__":
    check_domains()
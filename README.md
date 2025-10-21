# Domain Watchdog 
[![Check Domain Expiry](https://github.com/TansiqLabs/domain-watchdog/actions/workflows/check.yml/badge.svg)](https://github.com/TansiqLabs/domain-watchdog/actions/workflows/check.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A simple, serverless domain expiration monitor using Python and GitHub Actions. It checks a secret list of domains daily and sends alerts to multiple platforms (Telegram, Discord, Slack) if any domain is nearing its expiration date.

This repository is a **template**. You can use it to create your own monitor with **zero cost**, **no server required**, and keep your domain list **private**.

## 🚀 How to Use This Template

You only need to set **two secrets**.

### Step 1: Create Your Repository
Click the **"Use this template"** button at the top of this page and create a new repository under your own account.

### Step 2: Set Your Domain List (Private)
Your domain list is kept private using GitHub Secrets.

1.  Go to your new repository's **Settings** > **Secrets and variables** > **Actions**.
2.  Click **New repository secret**.
3.  **Name:** `DOMAINS_LIST`
4.  **Secret (Value):** Paste your domains here, **one per line**.
    ```
    # You can add comments
    your-domain.com
    another-domain.org
    example.dev
    ```

### Step 3: Configure Notifications (Choose One or More)
Add secrets for **all** the notification services you want to use. Alerts will be sent to every service you configure.

Go to your repository's **Settings** > **Secrets and variables** > **Actions** and add the secrets for your chosen service(s):

---
#### Option 1: Telegram
1.  Create a bot with **@BotFather** on Telegram to get a token.
2.  Send `/start` to your new bot.
3.  Find your `CHAT_ID` by visiting `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`.
4.  Add these **two** secrets to GitHub:
    * `TELEGRAM_BOT_TOKEN`: (Your bot token)
    * `TELEGRAM_CHAT_ID`: (Your chat ID)

---
#### Option 2: Discord
1.  In your Discord server, go to `Server Settings` > `Integrations` > `Webhooks`.
2.  Create a new webhook and copy its URL.
3.  Add this **one** secret to GitHub:
    * `DISCORD_WEBHOOK_URL`: (Your webhook URL)

---
#### Option 3: Slack
1.  Go to `https://api.slack.com/apps`, create a new app.
2.  Enable `Incoming Webhooks` and add a new webhook to your workspace.
3.  Copy the Webhook URL.
4.  Add this **one** secret to GitHub:
    * `SLACK_WEBHOOK_URL`: (Your webhook URL)

**That's it!** The monitor will automatically run daily. You can also run it manually from the **Actions** tab.

## 🔧 Customization (Optional)

If you want to change the notification schedule, edit the `check_domains.py` file:

```python
# A. Notify on these specific days
NOTIFY_SPECIFIC_DAYS = [60, 45, 30, 15]

# B. Start sending daily notifications this many days before expiry
# (Setting this to 7 means alerts on days 7, 6, 5, 4, 3, 2, 1, and 0)
NOTIFY_DAILY_BEFORE_DAYS = 7
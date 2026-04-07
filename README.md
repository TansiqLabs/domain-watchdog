# Domain Watchdog

Domain Watchdog is a lightweight Python monitor for domain and SSL expiry. It runs on GitHub Actions, reads domains from `domains.txt`, and sends alerts to Telegram, Discord, and Slack.

## Features

- Checks WHOIS domain expiry dates
- Checks SSL certificate expiry dates
- Supports Telegram, Discord, and Slack notifications
- Runs on a daily GitHub Actions schedule or on demand
- Keeps configuration simple with a plain `domains.txt` file

## Requirements

- Python 3.12 or later
- A GitHub repository with Actions enabled
- At least one notification service configured

## Setup

1. Add domains to `domains.txt`, one domain per line.
2. Add the notification secrets you want to use in GitHub Actions.
3. Run the workflow manually once from the Actions tab.

## Supported Secrets

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `DISCORD_WEBHOOK_URL`
- `SLACK_WEBHOOK_URL`

## Schedule

The workflow runs daily at `22:00 UTC` and can also be triggered manually.

## Local Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python check_domains.py
```

## Notes

- `domains.txt` supports blank lines and comment lines starting with `#`.
- WHOIS and SSL alerts use separate notification thresholds in `check_domains.py`.
- The GitHub Actions workflow uses Python 3.12 with pip caching.

## Support

Developed by Tansiq Labs.

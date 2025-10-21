# Domain Watchdog 
[![Check Domain Expiry](https://github.com/TansiqLabs/domain-watchdog/actions/workflows/check.yml/badge.svg)](https://github.com/TansiqLabs/domain-watchdog/actions/workflows/check.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A simple, serverless domain expiration monitor using Python and GitHub Actions. It checks a list of domains daily and sends an alert to a webhook (like Discord or Slack) if any domain is nearing its expiration date.

This repository is a **template**. You can use it to create your own monitor with **zero cost** and **no server required**.

## 🚀 How to Use This Template

You only need to edit **one file** and set **one secret**.

### Step 1: Create Your Repository
Click the **"Use this template"** button at the top of this page and create a new repository under your own account.

### Step 2: Add Your Domains
In your new repository, edit the `domains.txt` file. Add your domains, one per line.

### Step 3: Set Your Webhook Secret
1.  Go to your repository's **Settings** > **Secrets and variables** > **Actions**.
2.  Click **New repository secret**.
3.  **Name:** `WEBHOOK_URL`
4.  **Secret (Value):** Paste your incoming webhook URL (e.g., from Discord or Slack).
5.  Click **Add secret**.

**That's it!** The monitor will automatically run every day at 22:00 UTC (4:00 AM BST).

---

## ⚙️ How It Works
* A **GitHub Actions** workflow (`.github/workflows/check.yml`) runs on a daily schedule.
* The action runs the `check_domains.py` script.
* The script reads your domain list from `domains.txt`.
* It performs a **WHOIS lookup** for each domain.
* If a domain's expiration date matches a day in the `NOTIFY_DAYS` list (inside the script), it sends an alert via the `WEBHOOK_URL` secret.

## 🔧 Customization (Optional)

If you want to change the notification schedule:
1.  Open `check_domains.py`.
2.  Edit the `NOTIFY_DAYS` list.
    ```python
    # Notify 60, 30, 15, and daily for the last 7 days
    NOTIFY_DAYS = [60, 30, 15, 7, 6, 5, 4, 3, 2, 1, 0]
    ```

## 🔄 How to Update (For Forks)

If you **forked** this repository (instead of using it as a template), you can easily pull updates from this main repository without creating merge conflicts with your `domains.txt` file.

1.  **Configure Upstream:** Add this repository as the "upstream" remote (only need to do this once).
    ```bash
    git remote add upstream [https://github.com/TansiqLabs/domain-watchdog.git](https://github.com/TansiqLabs/domain-watchdog.git)
    ```
2.  **Pull Updates:** Fetch and merge changes from the upstream `main` branch.
    ```bash
    git fetch upstream
    git merge upstream/main
    ```

## 📄 License
This project is open-source and licensed under the **MIT License**.
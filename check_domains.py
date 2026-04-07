from __future__ import annotations

import datetime as dt
import os
import socket
import ssl
from pathlib import Path
from typing import Iterable

import requests
import whois

DOMAIN_FILE = Path("domains.txt")

NOTIFY_WHOIS_SPECIFIC_DAYS = {60, 45, 30, 15}
NOTIFY_WHOIS_DAILY_BEFORE_DAYS = 10

NOTIFY_SSL_SPECIFIC_DAYS = {30, 15, 7}
NOTIFY_SSL_DAILY_BEFORE_DAYS = 3

REQUEST_TIMEOUT_SECONDS = 10
SSL_TIMEOUT_SECONDS = 5

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")


def get_domains_from_file(filename: Path) -> list[str]:
    domains: list[str] = []
    try:
        for line in filename.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                domains.append(line)
        print(f"Successfully loaded {len(domains)} domains from {filename}.")
    except FileNotFoundError:
        print(f"ERROR: Domain file '{filename}' not found.")
    except OSError as exc:
        print(f"ERROR: Could not read domain file: {exc}")
    return domains


def escape_telegram_markdown(message: str) -> str:
    reserved = r"_[]()~`>#+-=|{}.!"
    escaped = message
    for char in reserved:
        escaped = escaped.replace(char, f"\\{char}")
    return escaped


def post_json(url: str, payload: dict[str, object]) -> requests.Response:
    return requests.post(url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)


def send_telegram_message(message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": escape_telegram_markdown(message),
        "parse_mode": "MarkdownV2",
    }
    try:
        response = post_json(url, payload)
        response.raise_for_status()
        print("Telegram message sent successfully.")
    except requests.RequestException as exc:
        print(f"Failed to send Telegram message: {exc}")


def send_discord_webhook(message: str) -> None:
    try:
        response = post_json(DISCORD_WEBHOOK_URL, {"content": message})
        response.raise_for_status()
        print("Discord message sent successfully.")
    except requests.RequestException as exc:
        print(f"Failed to send Discord message: {exc}")


def send_slack_webhook(message: str) -> None:
    try:
        response = post_json(SLACK_WEBHOOK_URL, {"text": message.replace('**', '*')})
        response.raise_for_status()
        print("Slack message sent successfully.")
    except requests.RequestException as exc:
        print(f"Failed to send Slack message: {exc}")


def send_notification(message: str) -> None:
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


def normalize_expiry_date(value: object) -> dt.datetime | None:
    if isinstance(value, list):
        for item in value:
            normalized = normalize_expiry_date(item)
            if normalized is not None:
                return normalized
        return None

    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=dt.timezone.utc)
        return value.astimezone(dt.timezone.utc)

    if isinstance(value, dt.date):
        return dt.datetime.combine(value, dt.time.min, tzinfo=dt.timezone.utc)

    return None


def should_notify(days_left: int, specific_days: set[int], daily_before_days: int) -> bool:
    return days_left in specific_days or 0 <= days_left <= daily_before_days


def format_domain_alert(domain_name: str, days_left: int, expiry_date: dt.datetime) -> str:
    return (
        "Domain Alert\n"
        f"{domain_name} will expire in {days_left} days.\n"
        f"Expiration date: {expiry_date.date()}"
    )


def format_ssl_alert(domain_name: str, days_left: int, expiry_date: dt.datetime) -> str:
    return (
        "SSL Alert\n"
        f"{domain_name} SSL certificate will expire in {days_left} days.\n"
        f"Expiration date: {expiry_date.date()}"
    )


def check_whois_expiry(domain_name: str, today_utc: dt.datetime) -> str | None:
    try:
        record = whois.whois(domain_name)
        expiry_date = normalize_expiry_date(record.expiration_date)
        if expiry_date is None:
            print("  [WHOIS] Expiration date not found.")
            return None

        days_left = (expiry_date - today_utc).days
        print(f"  [WHOIS] Days left: {days_left} (Expires on: {expiry_date.date()})")

        if should_notify(days_left, NOTIFY_WHOIS_SPECIFIC_DAYS, NOTIFY_WHOIS_DAILY_BEFORE_DAYS):
            return format_domain_alert(domain_name, days_left, expiry_date)
    except Exception as exc:
        print(f"  [WHOIS] Error checking: {exc}")
        return f"WHOIS check failed for {domain_name}: {exc}"
    return None


def check_ssl_expiry(domain_name: str, today_utc: dt.datetime) -> str | None:
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain_name, 443), timeout=SSL_TIMEOUT_SECONDS) as sock:
            with context.wrap_socket(sock, server_hostname=domain_name) as ssl_sock:
                cert = ssl_sock.getpeercert()

        expiry_date = dt.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        expiry_date = expiry_date.replace(tzinfo=dt.timezone.utc)
        days_left = (expiry_date - today_utc).days
        print(f"  [SSL] Days left: {days_left} (Expires on: {expiry_date.date()})")

        if should_notify(days_left, NOTIFY_SSL_SPECIFIC_DAYS, NOTIFY_SSL_DAILY_BEFORE_DAYS):
            return format_ssl_alert(domain_name, days_left, expiry_date)
    except socket.timeout:
        print(f"  [SSL] Timeout checking {domain_name} (Port 443).")
        return f"SSL check timed out for {domain_name}."
    except (ssl.SSLError, socket.gaierror, OSError) as exc:
        print(f"  [SSL] Error checking {domain_name}: {exc}")
        return f"SSL check failed for {domain_name}: {exc}"
    except Exception as exc:
        print(f"  [SSL] Unknown error checking {domain_name}: {exc}")
        return f"Unknown SSL error for {domain_name}: {exc}"
    return None


def check_all_domains(domains_to_check: Iterable[str]) -> None:
    today_utc = dt.datetime.now(dt.timezone.utc)
    alerts: list[str] = []
    print(f"Today's date: {today_utc.date()}. Starting all checks...")

    for domain_name in domains_to_check:
        print(f"--- Checking: {domain_name} ---")
        whois_alert = check_whois_expiry(domain_name, today_utc)
        if whois_alert:
            alerts.append(whois_alert)

        ssl_alert = check_ssl_expiry(domain_name, today_utc)
        if ssl_alert:
            alerts.append(ssl_alert)

    if alerts:
        send_notification("\n\n".join(alerts))
    else:
        print("All domains and SSL certs are fine. No alerts.")


if __name__ == "__main__":
    domains = get_domains_from_file(DOMAIN_FILE)
    if not domains:
        print("No domains to check. Exiting.")
    else:
        check_all_domains(domains)

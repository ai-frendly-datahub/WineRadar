from __future__ import annotations

import smtplib
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from typing import Any

import requests

from collectors.base import RawItem


@dataclass
class NotificationConfig:
    enabled: bool
    channels: list[str]
    email_settings: dict[str, Any] = field(default_factory=dict)
    webhook_url: str = ""
    telegram_config: dict[str, str] = field(default_factory=dict)
    rules: dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationEvent:
    title: str
    message: str
    priority: str
    event_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


class Notifier:
    def __init__(self, config: NotificationConfig):
        self.config = config

    def send(
        self,
        title: str,
        message: str,
        priority: str = "normal",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not self.config.enabled:
            return

        payload = {
            "title": title,
            "message": message,
            "priority": priority,
            "metadata": metadata or {},
        }

        channels = {channel.strip().lower() for channel in self.config.channels}
        if "email" in channels:
            self._send_email(payload)
        if "webhook" in channels:
            self._send_webhook(payload)
        if "telegram" in channels:
            self._send_telegram(payload)

    def _send_email(self, payload: dict[str, Any]) -> None:
        settings = self.config.email_settings
        smtp_host = str(settings.get("smtp_host", "")).strip()
        smtp_port = int(settings.get("smtp_port", 587) or 587)
        from_address = str(settings.get("from_address", "")).strip()
        to_addresses = settings.get("to_addresses", [])
        username = str(settings.get("username", "")).strip()
        password = str(settings.get("password", "")).strip()

        if (
            not smtp_host
            or not from_address
            or not isinstance(to_addresses, list)
            or not to_addresses
        ):
            return

        msg = MIMEText(str(payload["message"]), "plain", "utf-8")
        msg["Subject"] = str(payload["title"])
        msg["From"] = from_address
        msg["To"] = ", ".join(str(addr) for addr in to_addresses)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(msg)

    def _send_webhook(self, payload: dict[str, Any]) -> None:
        if not self.config.webhook_url:
            return
        requests.post(self.config.webhook_url, json=payload, timeout=10)

    def _send_telegram(self, payload: dict[str, Any]) -> None:
        token = self.config.telegram_config.get("bot_token", "")
        chat_id = self.config.telegram_config.get("chat_id", "")
        if not token or not chat_id:
            return

        text = f"[{payload['priority'].upper()}] {payload['title']}\n{payload['message']}"
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )


def detect_wine_notifications(
    items: list[RawItem],
    *,
    known_urls: set[str],
    rules: dict[str, Any],
) -> list[NotificationEvent]:
    """Detect wine-specific notification events.

    Args:
        items: List of collected raw items
        known_urls: Set of previously known URLs
        rules: Notification rules from config/notifications.yaml

    Returns:
        List of notification events to send
    """
    events: list[NotificationEvent] = []

    watched_regions = {
        str(region).strip() for region in rules.get("watched_regions", []) if str(region).strip()
    }
    high_trust_tiers = {
        str(tier).strip()
        for tier in rules.get("high_trust_tiers", ["T1_authoritative"])
        if str(tier).strip()
    }
    market_keywords = [
        str(keyword).strip().lower()
        for keyword in rules.get("market_keywords", [])
        if str(keyword).strip()
    ]

    for item in items:
        region = item["region"].strip() if item.get("region") else ""
        title = item["title"].strip()
        trust_tier = str(item.get("trust_tier", "")).strip()

        if item["url"] not in known_urls and region:
            region_ok = not watched_regions or any(wr in region for wr in watched_regions)
            if region_ok:
                events.append(
                    NotificationEvent(
                        title=f"[WineRadar] New content: {title}",
                        message=(
                            f"Region: {region}\n"
                            f"Source: {item.get('source_name', 'unknown')}\n"
                            f"URL: {item['url']}"
                        ),
                        priority="normal",
                        event_type="new_content",
                        metadata={"region": region, "url": item["url"]},
                    )
                )

        if trust_tier in high_trust_tiers and item["url"] not in known_urls:
            events.append(
                NotificationEvent(
                    title=f"[WineRadar] Authoritative source: {title}",
                    message=(
                        f"Trust tier: {trust_tier}\n"
                        f"Source: {item.get('source_name', 'unknown')}\n"
                        f"URL: {item['url']}"
                    ),
                    priority="high",
                    event_type="high_trust_content",
                    metadata={"trust_tier": trust_tier, "url": item["url"]},
                )
            )

        haystack = f"{item['title']}\n{item.get('summary') or ''}".lower()
        if any(keyword in haystack for keyword in market_keywords):
            events.append(
                NotificationEvent(
                    title=f"[WineRadar] Market signal: {title}",
                    message=f"Market-related keywords detected.\nURL: {item['url']}",
                    priority="normal",
                    event_type="market_trend",
                    metadata={"url": item["url"]},
                )
            )

    return events

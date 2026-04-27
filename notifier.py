# Canonical Notifier implementation for AI-Friendly DataHub
# Synced from: Radar-Template/radar/notifier.py
# DO NOT MODIFY core classes (Notifier, NotificationPayload, EmailNotifier, WebhookNotifier, CompositeNotifier)
# Domain-specific detection functions (detect_wine_notifications) preserved below

from __future__ import annotations

import smtplib
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.text import MIMEText
from typing import Any, Protocol

import requests
import structlog

from collectors.base import RawItem


logger = structlog.get_logger(__name__)


@dataclass
class NotificationPayload:
    """Payload for notification delivery."""

    category_name: str
    sources_count: int
    collected_count: int
    matched_count: int
    errors_count: int
    timestamp: datetime
    report_url: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Convert payload to dictionary for JSON serialization."""
        return {
            "category_name": self.category_name,
            "sources_count": self.sources_count,
            "collected_count": self.collected_count,
            "matched_count": self.matched_count,
            "errors_count": self.errors_count,
            "timestamp": self.timestamp.isoformat(),
            "report_url": self.report_url,
        }


class Notifier(Protocol):
    """Protocol for notification delivery."""

    def send(self, payload: NotificationPayload) -> bool:
        """Send notification. Return True if successful, False otherwise."""
        ...


class EmailNotifier:
    """Send notifications via email using SMTP."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_addr: str,
        to_addrs: list[str],
    ) -> None:
        """Initialize email notifier.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_addr: Sender email address
            to_addrs: List of recipient email addresses
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_addr = from_addr
        self.to_addrs = to_addrs

    def send(self, payload: NotificationPayload) -> bool:
        """Send email notification.

        Args:
            payload: Notification payload

        Returns:
            True if successful, False otherwise
        """
        try:
            subject = f"Radar Pipeline Complete: {payload.category_name}"
            body = self._build_email_body(payload)

            msg = MIMEText(body, "plain")
            msg["Subject"] = subject
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info("email_notification_sent", category=payload.category_name)
            return True
        except Exception as e:
            logger.error(
                "email_notification_failed",
                category=payload.category_name,
                error=str(e),
            )
            return False

    def _build_email_body(self, payload: NotificationPayload) -> str:
        """Build email body from payload."""
        lines = [
            "Radar Pipeline Completion Report",
            "================================",
            "",
            f"Category: {payload.category_name}",
            f"Timestamp: {payload.timestamp.isoformat()}",
            "",
            "Statistics:",
            f"  Sources: {payload.sources_count}",
            f"  Collected: {payload.collected_count}",
            f"  Matched: {payload.matched_count}",
            f"  Errors: {payload.errors_count}",
        ]
        if payload.report_url:
            lines.append("")
            lines.append(f"Report: {payload.report_url}")
        return "\n".join(lines)


class WebhookNotifier:
    """Send notifications via HTTP webhook."""

    def __init__(
        self,
        url: str,
        method: str = "POST",
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize webhook notifier.

        Args:
            url: Webhook URL
            method: HTTP method (POST or GET)
            headers: Optional HTTP headers
        """
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}

    def send(self, payload: NotificationPayload) -> bool:
        """Send webhook notification.

        Args:
            payload: Notification payload

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.method == "POST":
                response = requests.post(
                    self.url,
                    json=payload.to_dict(),
                    headers=self.headers,
                    timeout=10,
                )
            elif self.method == "GET":
                response = requests.get(
                    self.url,
                    headers=self.headers,
                    timeout=10,
                )
            else:
                logger.error(
                    "webhook_invalid_method",
                    method=self.method,
                    url=self.url,
                )
                return False

            if response.status_code >= 400:
                logger.error(
                    "webhook_notification_failed",
                    url=self.url,
                    status_code=response.status_code,
                )
                return False

            logger.info("webhook_notification_sent", url=self.url)
            return True
        except Exception as e:
            logger.error(
                "webhook_notification_failed",
                url=self.url,
                error=str(e),
            )
            return False


class CompositeNotifier:
    """Send notifications to multiple notifiers."""

    def __init__(self, notifiers: list[object]) -> None:
        """Initialize composite notifier.

        Args:
            notifiers: List of notifiers to send to
        """
        self.notifiers = notifiers

    def send(self, payload: NotificationPayload) -> bool:
        """Send notification to all notifiers.

        Args:
            payload: Notification payload

        Returns:
            True if all notifiers succeeded, False if any failed
        """
        if not self.notifiers:
            return True

        results = []
        for notifier in self.notifiers:
            try:
                result = notifier.send(payload)
                results.append(result)
            except Exception:
                results.append(False)
        return all(results) if results else True


# Domain-specific configuration and event classes (preserved from original)
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


def detect_wine_notifications(
    items: list[RawItem],
    *,
    known_urls: set[str],
    rules: dict[str, Any],
) -> list[NotificationEvent]:
    """Detect wine-specific notification events (new content, trust tier).

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

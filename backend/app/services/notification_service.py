"""
通知渠道服务。
支持企业微信、钉钉、飞书机器人和邮件通知。
"""

import logging
import smtplib
from email.mime.text import MIMEText
from typing import Optional

import httpx
from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.alert import Alert, NotificationChannel

logger = logging.getLogger(__name__)


class NotificationService:
    """多渠道告警通知。"""

    async def send_alert(self, alert: Alert) -> None:
        """向所有启用的通知渠道发送告警。"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(NotificationChannel).where(
                    NotificationChannel.is_enabled == True  # noqa: E712
                )
            )
            channels = result.scalars().all()

        for channel in channels:
            try:
                if channel.channel_type in ("wechat", "dingtalk", "feishu"):
                    await self._send_webhook(channel, alert)
                elif channel.channel_type == "email":
                    await self._send_email(channel, alert)
            except Exception as e:
                logger.error("通知发送失败 [%s]: %s", channel.name, e)

    async def _send_webhook(self, channel: NotificationChannel, alert: Alert) -> None:
        """通过 Webhook 发送机器人消息。"""
        if not channel.webhook_url:
            return

        severity_emoji = {"critical": "🔴", "warning": "🟠", "info": "🔵"}.get(alert.severity, "⚪")

        if channel.channel_type == "wechat":
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": (
                        f"### {severity_emoji} 数据库监控告警\n"
                        f"> **实例**: {alert.instance_name}\n"
                        f"> **级别**: {alert.severity}\n"
                        f"> **内容**: {alert.message}\n"
                        f"> **根因**: {alert.root_cause}\n"
                        f"> **建议**: {alert.suggestion}\n"
                        f"> **时间**: {alert.created_at}"
                    )
                },
            }
        elif channel.channel_type == "dingtalk":
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"数据库告警 - {alert.instance_name}",
                    "text": (
                        f"### {severity_emoji} {alert.title}\n"
                        f"- 级别: {alert.severity}\n"
                        f"- 内容: {alert.message}\n"
                        f"- 建议: {alert.suggestion}"
                    ),
                },
            }
        else:  # feishu
            payload = {
                "msg_type": "text",
                "content": {
                    "text": (
                        f"{severity_emoji} 数据库监控告警\n"
                        f"实例: {alert.instance_name}\n"
                        f"级别: {alert.severity}\n"
                        f"内容: {alert.message}\n"
                        f"建议: {alert.suggestion}"
                    )
                },
            }

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(channel.webhook_url, json=payload)
            if resp.status_code != 200:
                logger.error("Webhook 响应异常: %s %s", resp.status_code, resp.text)

    async def _send_email(self, channel: NotificationChannel, alert: Alert) -> None:
        """发送邮件通知。"""
        settings = get_settings()
        if not settings.smtp_host or not channel.email_recipients:
            return

        msg = MIMEText(
            f"数据库监控告警\n\n"
            f"实例: {alert.instance_name}\n"
            f"级别: {alert.severity}\n"
            f"内容: {alert.message}\n"
            f"根因分析: {alert.root_cause}\n"
            f"优化建议: {alert.suggestion}\n"
            f"时间: {alert.created_at}",
            "plain",
            "utf-8",
        )
        msg["Subject"] = f"[DB Monitor] {alert.title}"
        msg["From"] = settings.smtp_from or settings.smtp_user
        recipients = [e.strip() for e in channel.email_recipients.split(",") if e.strip()]
        msg["To"] = ", ".join(recipients)

        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(msg["From"], recipients, msg.as_string())
        except Exception as e:
            logger.error("邮件发送失败: %s", e)


notification_service = NotificationService()

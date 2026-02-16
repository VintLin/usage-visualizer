#!/usr/bin/env python3
"""
Multi-channel notification module for LLM Cost Monitor
Supports: Feishu, Telegram, Discord, Slack, Webhook, Console
"""
import os
import sys
import json
import requests
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class NotificationChannel(ABC):
    """Base class for notification channels"""
    
    @abstractmethod
    def send(self, message: str, **kwargs) -> bool:
        """Send notification. Returns True if successful."""
        pass


class ConsoleChannel(NotificationChannel):
    """Console output (for testing)"""
    
    def send(self, message: str, **kwargs) -> bool:
        print(f"[CONSOLE] {message}")
        return True


class FeishuChannel(NotificationChannel):
    """Feishu (飞书) notification"""
    
    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or os.environ.get("FEISHU_APP_ID")
        self.app_secret = app_secret or os.environ.get("FEISHU_APP_SECRET")
    
    def _get_token(self) -> Optional[str]:
        if not self.app_id or not self.app_secret:
            return None
        try:
            resp = requests.post(
                "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                json={"app_id": self.app_id, "app_secret": self.app_secret},
                timeout=10
            )
            data = resp.json()
            return data.get("tenant_access_token") if data.get("code") == 0 else None
        except:
            return None
    
    def send(self, message: str, receive_id: str = None, **kwargs) -> bool:
        if not self.app_id:
            print("[Feishu] No app_id configured")
            return False
        
        token = self._get_token()
        if not token:
            print("[Feishu] Failed to get token")
            return False
        
        # Try image first
        image_path = kwargs.get("image_path")
        
        try:
            if image_path:
                # Upload and send image
                with open(image_path, "rb") as f:
                    files = {"image": f}
                    data = {"image_type": "message"}
                    headers = {"Authorization": f"Bearer {token}"}
                    resp = requests.post(
                        "https://open.feishu.cn/open-apis/im/v1/images",
                        files=files, data=data, headers=headers, timeout=30
                    )
                    result = resp.json()
                    if result.get("code") == 0:
                        image_key = result["data"]["image_key"]
                        # Send image message
                        msg_data = {
                            "msg_type": "image",
                            "receive_id": receive_id or os.environ.get("FEISHU_USER_ID"),
                            "content": json.dumps({"image_key": image_key})
                        }
                        requests.post(
                            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
                            headers=headers, json=msg_data, timeout=10
                        )
            
            # Send text message
            msg_data = {
                "msg_type": "text",
                "receive_id": receive_id or os.environ.get("FEISHU_USER_ID"),
                "content": json.dumps({"text": message})
            }
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.post(
                "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
                headers=headers, json=msg_data, timeout=10
            )
            return resp.json().get("code") == 0
        except Exception as e:
            print(f"[Feishu] Error: {e}")
            return False


class TelegramChannel(NotificationChannel):
    """Telegram notification"""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    
    def send(self, message: str, **kwargs) -> bool:
        if not self.bot_token or not self.chat_id:
            print("[Telegram] No bot_token or chat_id configured")
            return False
        
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={"chat_id": self.chat_id, "text": message},
                timeout=10
            )
            return resp.json().get("ok", False)
        except Exception as e:
            print(f"[Telegram] Error: {e}")
            return False


class DiscordChannel(NotificationChannel):
    """Discord webhook notification"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.environ.get("DISCORD_WEBHOOK_URL")
    
    def send(self, message: str, **kwargs) -> bool:
        if not self.webhook_url:
            print("[Discord] No webhook_url configured")
            return False
        
        try:
            resp = requests.post(
                self.webhook_url,
                json={"content": message},
                timeout=10
            )
            return resp.status_code in (200, 204)
        except Exception as e:
            print(f"[Discord] Error: {e}")
            return False


class SlackChannel(NotificationChannel):
    """Slack webhook notification"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    
    def send(self, message: str, **kwargs) -> bool:
        if not self.webhook_url:
            print("[Slack] No webhook_url configured")
            return False
        
        try:
            resp = requests.post(
                self.webhook_url,
                json={"text": message},
                timeout=10
            )
            return resp.status_code in (200, 204)
        except Exception as e:
            print(f"[Slack] Error: {e}")
            return False


class WebhookChannel(NotificationChannel):
    """Generic webhook notification"""
    
    def __init__(self, url: str = None, headers: Dict = None):
        self.url = url or os.environ.get("CUSTOM_WEBHOOK_URL")
        self.headers = headers or {}
    
    def send(self, message: str, **kwargs) -> bool:
        if not self.url:
            print("[Webhook] No URL configured")
            return False
        
        try:
            data = kwargs.get("json", {"text": message})
            resp = requests.post(
                self.url,
                json=data,
                headers=self.headers,
                timeout=10
            )
            return resp.status_code in (200, 201, 204)
        except Exception as e:
            print(f"[Webhook] Error: {e}")
            return False


# Channel registry
CHANNELS = {
    "console": ConsoleChannel,
    "feishu": FeishuChannel,
    "telegram": TelegramChannel,
    "discord": DiscordChannel,
    "slack": SlackChannel,
    "webhook": WebhookChannel,
}


def get_channel(name: str, **config) -> Optional[NotificationChannel]:
    """Get notification channel by name"""
    channel_class = CHANNELS.get(name.lower())
    if channel_class:
        return channel_class(**config)
    return None


def send_notification(
    message: str,
    channels: list = None,
    **kwargs
) -> Dict[str, bool]:
    """
    Send notification to multiple channels
    
    Args:
        message: Message to send
        channels: List of channel names (default: ["console"])
        **kwargs: Additional args passed to channels
    
    Returns:
        Dict mapping channel name to success status
    """
    channels = channels or ["console"]
    results = {}
    
    for name in channels:
        channel = get_channel(name)
        if channel:
            results[name] = channel.send(message, **kwargs)
        else:
            results[name] = False
            print(f"[Notification] Unknown channel: {name}")
    
    return results


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Send notification")
    parser.add_argument("--message", "-m", required=True, help="Message to send")
    parser.add_argument("--channel", "-c", default="console", help="Channel (comma-separated)")
    parser.add_argument("--image", help="Image path to send (Feishu)")
    
    args = parser.parse_args()
    
    channel_list = [c.strip() for c in args.channel.split(",")]
    results = send_notification(
        args.message, 
        channels=channel_list,
        image_path=args.image
    )
    
    for ch, ok in results.items():
        print(f"{ch}: {'✓' if ok else '✗'}")

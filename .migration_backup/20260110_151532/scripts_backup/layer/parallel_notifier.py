"""
Orion ODA V3 - Parallel Session Notifier
=========================================
System notifications for parallel agent execution.

Maps to Boris Cherny's pattern:
"I run 5 Claudes in parallel in my terminal.
I number my tabs 1-5, and use system notifications to know when a Claude needs input."

Usage:
    notifier = ParallelNotifier()
    await notifier.notify_wave_complete(wave_number=1, success_count=4, total=5)
    await notifier.notify_agent_needs_input(tab_id=3, task="Review authentication")
"""

import asyncio
import logging
import os
import platform
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Types of notifications."""
    WAVE_COMPLETE = "wave_complete"
    AGENT_NEEDS_INPUT = "agent_needs_input"
    AGENT_FAILED = "agent_failed"
    AGENT_SUCCESS = "agent_success"
    SESSION_HEALTH_WARNING = "session_health_warning"


@dataclass
class Notification:
    """Represents a notification to be sent."""
    type: NotificationType
    title: str
    message: str
    tab_id: Optional[int] = None
    urgency: str = "normal"  # low, normal, critical

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "tab_id": self.tab_id,
            "urgency": self.urgency,
        }


class ParallelNotifier:
    """
    Manages system notifications for parallel agent sessions.

    Supports:
    - Linux: notify-send (libnotify)
    - macOS: osascript (AppleScript)
    - Windows: PowerShell toast notifications
    - WebSocket: For observe server integration

    Boris Cherny Pattern Implementation:
    - Tab numbering (1-5)
    - System notifications on wave complete
    - Input request notifications
    """

    def __init__(
        self,
        websocket_url: Optional[str] = None,
        enable_desktop: bool = True,
        enable_websocket: bool = True,
    ):
        self.websocket_url = websocket_url or os.getenv(
            "ORION_OBSERVE_WS",
            "ws://localhost:8765"
        )
        self.enable_desktop = enable_desktop
        self.enable_websocket = enable_websocket
        self._platform = platform.system().lower()
        self._notification_history: List[Notification] = []
        self._callbacks: Dict[NotificationType, List[Callable]] = {}

    def register_callback(
        self,
        notification_type: NotificationType,
        callback: Callable,
    ) -> None:
        """Register a callback for a notification type."""
        if notification_type not in self._callbacks:
            self._callbacks[notification_type] = []
        self._callbacks[notification_type].append(callback)

    async def notify(self, notification: Notification) -> bool:
        """
        Send a notification through all enabled channels.

        Returns:
            True if at least one channel succeeded
        """
        self._notification_history.append(notification)
        success = False

        # Desktop notification
        if self.enable_desktop:
            try:
                await self._send_desktop_notification(notification)
                success = True
            except Exception as e:
                logger.warning(f"Desktop notification failed: {e}")

        # WebSocket notification (for observe server)
        if self.enable_websocket:
            try:
                await self._send_websocket_notification(notification)
                success = True
            except Exception as e:
                logger.debug(f"WebSocket notification skipped: {e}")

        # Trigger callbacks
        await self._trigger_callbacks(notification)

        return success

    async def notify_wave_complete(
        self,
        wave_number: int,
        success_count: int,
        total: int,
        failed_tasks: Optional[List[str]] = None,
    ) -> bool:
        """
        Notify when a wave of parallel agents completes.

        Boris Cherny pattern: System notification when Claude completes.
        """
        status = "SUCCESS" if success_count == total else "PARTIAL"
        urgency = "normal" if success_count == total else "critical"

        message = f"Wave {wave_number}: {success_count}/{total} agents completed"
        if failed_tasks:
            message += f"\nFailed: {', '.join(failed_tasks[:3])}"
            if len(failed_tasks) > 3:
                message += f" (+{len(failed_tasks) - 3} more)"

        notification = Notification(
            type=NotificationType.WAVE_COMPLETE,
            title=f"🌊 Wave {wave_number} {status}",
            message=message,
            urgency=urgency,
        )

        return await self.notify(notification)

    async def notify_agent_needs_input(
        self,
        tab_id: int,
        task: str,
        context: Optional[str] = None,
    ) -> bool:
        """
        Notify when an agent needs user input.

        Boris Cherny pattern: "Use system notifications to know when a Claude needs input"
        """
        message = f"Tab {tab_id} needs input for:\n{task[:100]}"
        if context:
            message += f"\n\nContext: {context[:50]}..."

        notification = Notification(
            type=NotificationType.AGENT_NEEDS_INPUT,
            title=f"🔔 Tab {tab_id} Awaiting Input",
            message=message,
            tab_id=tab_id,
            urgency="critical",
        )

        return await self.notify(notification)

    async def notify_agent_failed(
        self,
        tab_id: int,
        task: str,
        error: str,
    ) -> bool:
        """Notify when an agent fails."""
        notification = Notification(
            type=NotificationType.AGENT_FAILED,
            title=f"❌ Tab {tab_id} Failed",
            message=f"Task: {task[:50]}...\nError: {error[:100]}",
            tab_id=tab_id,
            urgency="critical",
        )

        return await self.notify(notification)

    async def notify_agent_success(
        self,
        tab_id: int,
        task: str,
        duration_seconds: float,
    ) -> bool:
        """Notify when an agent succeeds."""
        notification = Notification(
            type=NotificationType.AGENT_SUCCESS,
            title=f"✅ Tab {tab_id} Complete",
            message=f"Task: {task[:50]}...\nDuration: {duration_seconds:.1f}s",
            tab_id=tab_id,
            urgency="low",
        )

        return await self.notify(notification)

    async def notify_session_health_warning(
        self,
        session_id: str,
        warning: str,
        recommendation: str,
    ) -> bool:
        """Notify about session health issues (Pattern 12 integration)."""
        notification = Notification(
            type=NotificationType.SESSION_HEALTH_WARNING,
            title="⚠️ Session Health Warning",
            message=f"Session: {session_id[:8]}...\n{warning}\n\nRecommend: {recommendation}",
            urgency="critical",
        )

        return await self.notify(notification)

    async def _send_desktop_notification(self, notification: Notification) -> None:
        """Send desktop notification based on platform."""
        if self._platform == "linux":
            await self._send_linux_notification(notification)
        elif self._platform == "darwin":
            await self._send_macos_notification(notification)
        elif self._platform == "windows":
            await self._send_windows_notification(notification)
        else:
            logger.warning(f"Unsupported platform for desktop notifications: {self._platform}")

    async def _send_linux_notification(self, notification: Notification) -> None:
        """Send notification via notify-send (Linux)."""
        urgency_map = {"low": "low", "normal": "normal", "critical": "critical"}

        cmd = [
            "notify-send",
            "--urgency", urgency_map.get(notification.urgency, "normal"),
            "--app-name", "Orion ODA",
            notification.title,
            notification.message,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.wait()

    async def _send_macos_notification(self, notification: Notification) -> None:
        """Send notification via osascript (macOS)."""
        script = f'''
        display notification "{notification.message}" with title "{notification.title}" sound name "default"
        '''

        process = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.wait()

    async def _send_windows_notification(self, notification: Notification) -> None:
        """Send notification via PowerShell (Windows)."""
        script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
        $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
        $xml.GetElementsByTagName("text")[0].AppendChild($xml.CreateTextNode("{notification.title}")) | Out-Null
        $xml.GetElementsByTagName("text")[1].AppendChild($xml.CreateTextNode("{notification.message}")) | Out-Null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Orion ODA").Show($toast)
        '''

        process = await asyncio.create_subprocess_exec(
            "powershell", "-Command", script,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.wait()

    async def _send_websocket_notification(self, notification: Notification) -> None:
        """Send notification via WebSocket to observe server."""
        try:
            import websockets

            async with websockets.connect(self.websocket_url) as ws:
                import json
                await ws.send(json.dumps({
                    "type": "notification",
                    "payload": notification.to_dict(),
                }))
        except ImportError:
            logger.debug("websockets not installed, skipping WebSocket notification")
        except Exception as e:
            logger.debug(f"WebSocket notification failed: {e}")

    async def _trigger_callbacks(self, notification: Notification) -> None:
        """Trigger registered callbacks for notification type."""
        callbacks = self._callbacks.get(notification.type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification)
                else:
                    callback(notification)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def get_history(self, limit: int = 50) -> List[dict]:
        """Get notification history."""
        return [n.to_dict() for n in self._notification_history[-limit:]]


# Singleton instance for easy access
_notifier_instance: Optional[ParallelNotifier] = None


def get_notifier() -> ParallelNotifier:
    """Get the global notifier instance."""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = ParallelNotifier()
    return _notifier_instance


# CLI test
if __name__ == "__main__":
    async def test_notifications():
        notifier = ParallelNotifier()

        print("Testing wave complete notification...")
        await notifier.notify_wave_complete(
            wave_number=1,
            success_count=4,
            total=5,
            failed_tasks=["Fix authentication bug"],
        )

        print("Testing agent needs input notification...")
        await notifier.notify_agent_needs_input(
            tab_id=3,
            task="Review authentication changes",
            context="Waiting for approval on security-sensitive code",
        )

        print("Notifications sent!")

    asyncio.run(test_notifications())


from abc import ABC, abstractmethod
from typing import Any, Dict

class SideEffect(ABC):
    """
    Abstract Base Class for Side Effects (Webhooks, Notifications).
    Executed ONLY after successful Ontology Edits.
    """
    @abstractmethod
    def execute(self, context: Dict[str, Any]):
        pass

class NotificationEffect(SideEffect):
    """
    Sends a notification (Toast/Slack/Email).
    """
    def __init__(self, recipient_id: str, message_template: str):
        self.recipient_id = recipient_id
        self.message_template = message_template

    def execute(self, context: Dict[str, Any]):
        msg = self.message_template.format(**context)
        print(f"[Notification] To {self.recipient_id}: {msg}")

class WebhookEffect(SideEffect):
    """
    Triggers an external Webhook.
    """
    def __init__(self, url: str, method: str = "POST"):
        self.url = url
        self.method = method

    def execute(self, context: Dict[str, Any]):
        print(f"[Webhook] {self.method} {self.url} with {context}")

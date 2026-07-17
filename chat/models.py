"""chat.models

CHAT APP
========
AI chatbot conversation storage. Real-time message delivery is handled
separately by a Channels WebSocket consumer (to be added in chat/consumers.py
and chat/routing.py). This file only defines persistence models.

Cross-app references:
- ChatSession.user -> accounts.User
- ChatSession.active_child -> accounts.StudentProfile
"""

from django.db import models


class ChatSession(models.Model):
    """One conversation thread."""

    BOT_TYPE_CHOICES = (
        ("maintenance", "Maintenance & Help Desk Bot"),
        ("fee", "Fee Bot"),
        ("media", "Media Bot"),
        ("assignment", "Assignment Bot"),
        ("exam", "Exam Bot"),
        ("attendance", "Attendance & Compliance Bot"),
        ("certificate", "Certificates Bot"),
        ("scholarship", "Scholarship Bot"),
        ("inventory", "Inventory Bot"),
        ("event", "Event Bot"),
        ("general", "General Assistant"),
    )

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="chat_sessions")
    bot_type = models.CharField(max_length=20, choices=BOT_TYPE_CHOICES, default="general")
    title = models.CharField(max_length=200, blank=True)

    # Meaningful when user.role == Parent.
    active_child = models.ForeignKey(
        "accounts.StudentProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.user.email} ({self.created_at})"


class ChatMessage(models.Model):
    ROLE_CHOICES = (("user", "user"), ("assistant", "assistant"))

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.session.user.email} - {self.role} ({self.created_at})"


class PendingAction(models.Model):
    """Write-safety confirm flow: tool propose -> pending -> confirm/cancel."""

    class Status:
        PENDING = "pending"
        CONFIRMED = "confirmed"
        CANCELLED = "cancelled"

    STATUS_CHOICES = (
        (Status.PENDING, "Pending"),
        (Status.CONFIRMED, "Confirmed"),
        (Status.CANCELLED, "Cancelled"),
    )

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="pending_actions")
    tool_name = models.CharField(max_length=100, db_index=True)

    # params as JSON string (kept simple for migration safety).
    params = models.TextField()

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=Status.PENDING, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PendingAction({self.id}) {self.tool_name} [{self.status}]"


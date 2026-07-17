from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsParent
from communication.models import Message, Notification
from communication.serializers.message import (
    MessageSerializer,
    ConversationContactSerializer,
)
from communication.serializers.parent import ParentNotificationSerializer


# ── NOTIFICATIONS ─────────────────────────────────────────────

class ParentNotificationListView(generics.ListAPIView):
    """GET /api/parent/notifications"""
    serializer_class = ParentNotificationSerializer
    permission_classes = [IsParent]

    def get_queryset(self):
        return Notification.objects.filter(
            receiver=self.request.user
        ).order_by("-created_at")


# ── CONVERSATIONS ─────────────────────────────────────────────

class ParentConversationListView(generics.ListAPIView):
    """GET /api/parent/conversations"""
    serializer_class = ConversationContactSerializer
    permission_classes = [IsParent]

    def get_queryset(self):
        return Message.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        ).order_by("-created_at")


class ParentMessageThreadView(generics.ListAPIView):
    """GET /api/parent/messages/<conversation_id>"""
    serializer_class = MessageSerializer
    permission_classes = [IsParent]

    def get_queryset(self):
        conversation_id = self.kwargs["conversation_id"]
        return Message.objects.filter(conversation_id=conversation_id).order_by("created_at")


class ParentMarkMessageReadView(APIView):
    """POST /api/parent/messages/<message_id>/mark-read"""
    permission_classes = [IsParent]

    def post(self, request, message_id):
        message = get_object_or_404(Message, id=message_id, receiver=request.user)
        message.is_read = True
        message.save()
        return Response({"detail": "Message marked as read."}, status=200)

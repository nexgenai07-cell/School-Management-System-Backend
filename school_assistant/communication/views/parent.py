<<<<<<< HEAD
from rest_framework import generics
from accounts.permissions import IsParent
from communication.models import Notification
from communication.serializers.parent import ParentNotificationSerializer

class ParentNotificationListView(generics.ListAPIView):
    """Parents can view their own notifications (including child-related ones)."""
=======
"""
PARENT — COMMUNICATION VIEWS
================================
1. Notifications list  (pehle se tha)
2. Messages — Teacher ke saath chat:
   - Conversations list
   - Message thread (GET history + POST nayi message)
   - Mark message read
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsParent
from communication.models import Notification, Message
from communication.serializers.parent import ParentNotificationSerializer
from communication.serializers.message import (
    MessageSerializer,
    ConversationContactSerializer,
)


# ── NOTIFICATIONS (pehle se tha) ─────────────────────────────────────────────

class ParentNotificationListView(generics.ListAPIView):
    """GET /api/parent/notifications"""
>>>>>>> nimra-fix-develop
    serializer_class = ParentNotificationSerializer
    permission_classes = [IsParent]

    def get_queryset(self):
<<<<<<< HEAD
        return Notification.objects.filter(receiver=self.request.user).order_by("-created_at")
=======
        return Notification.objects.filter(
            receiver=self.request.user
        ).order_by("-created_at")


# ── MESSAGING ─────────────────────────────────────────────────────────────────

class ParentConversationListView(generics.ListAPIView):
    """
    GET /api/parent/messages/conversations
    Un saare teachers ki list jinkay saath parent ne baat ki hai.
    Frontend sidebar list ke liye (Page 37).
    """
    serializer_class = ConversationContactSerializer
    permission_classes = [IsParent]

    def get_queryset(self):
        user = self.request.user
        msgs = Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).values_list("sender_id", "receiver_id")

        other_ids = set()
        for sender_id, receiver_id in msgs:
            if sender_id == user.id:
                other_ids.add(receiver_id)
            else:
                other_ids.add(sender_id)

        return User.objects.filter(
            id__in=other_ids,
            role__role_name="Teacher"
        )


class ParentMessageThreadView(generics.ListCreateAPIView):
    """
    GET  /api/parent/messages/<teacher_id>
         Ek teacher ke saath poori conversation history.

    POST /api/parent/messages/<teacher_id>
         Is teacher ko nayi message bhejo.
         Body: { "content": "Mera beta kal absent tha..." }
    """
    serializer_class = MessageSerializer
    permission_classes = [IsParent]

    def get_queryset(self):
        other_id = self.kwargs["teacher_id"]
        return Message.objects.filter(
            Q(sender=self.request.user, receiver_id=other_id) |
            Q(sender_id=other_id, receiver=self.request.user)
        ).order_by("created_at")

    def perform_create(self, serializer):
        teacher_user = get_object_or_404(
            User,
            id=self.kwargs["teacher_id"],
            role__role_name="Teacher"
        )
        serializer.save(
            sender=self.request.user,
            receiver=teacher_user
        )


class ParentMarkMessageReadView(APIView):
    """
    PUT /api/parent/messages/read/<message_id>
    Sirf wo message read mark hoga jo is parent ko receive hua tha.
    """
    permission_classes = [IsParent]

    def put(self, request, message_id):
        msg = get_object_or_404(
            Message,
            id=message_id,
            receiver=request.user
        )
        msg.is_read = True
        msg.save()
        return Response(
            {"detail": "Message marked as read."},
            status=status.HTTP_200_OK
        )
>>>>>>> nimra-fix-develop

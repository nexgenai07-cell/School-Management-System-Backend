"""
TEACHER — COMMUNICATION VIEWS
================================
1. Notifications list  (pehle se tha, hata mat)
2. Messages — Parent ke saath chat:
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
from accounts.permissions import IsTeacher
from communication.models import Notification, Message
from communication.serializers.teacher import TeacherNotificationSerializer
from communication.serializers.message import (
    MessageSerializer,
    ConversationContactSerializer,
)


# ── NOTIFICATIONS (pehle se tha) ─────────────────────────────────────────────

class TeacherNotificationListView(generics.ListAPIView):
    """GET /api/teacher/notifications"""
    serializer_class = TeacherNotificationSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return Notification.objects.filter(
            receiver=self.request.user
        ).order_by("-created_at")


# ── MESSAGING ─────────────────────────────────────────────────────────────────

class TeacherConversationListView(generics.ListAPIView):
    """
    GET /api/teacher/messages/conversations
    Un saare parents ki list jinkay saath teacher ne baat ki hai.
    Frontend sidebar list ke liye (Page 20).
    """
    serializer_class = ConversationContactSerializer
    permission_classes = [IsTeacher]

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
            role__role_name="Parent"
        )


class TeacherMessageThreadView(generics.ListCreateAPIView):
    """
    GET  /api/teacher/messages/<parent_id>
         Ek parent ke saath poori conversation history.

    POST /api/teacher/messages/<parent_id>
         Is parent ko nayi message bhejo.
         Body: { "content": "Aap ke bache ki attendance..." }
    """
    serializer_class = MessageSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        other_id = self.kwargs["parent_id"]
        return Message.objects.filter(
            Q(sender=self.request.user, receiver_id=other_id) |
            Q(sender_id=other_id, receiver=self.request.user)
        ).order_by("created_at")

    def perform_create(self, serializer):
        # Confirm karo ke receiver actual Parent hai
        parent_user = get_object_or_404(
            User,
            id=self.kwargs["parent_id"],
            role__role_name="Parent"
        )
        serializer.save(
            sender=self.request.user,
            receiver=parent_user
        )


class TeacherMarkMessageReadView(APIView):
    """
    PUT /api/teacher/messages/read/<message_id>
    Sirf wo message read mark hoga jo is teacher ko receive hua tha.
    """
    permission_classes = [IsTeacher]

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
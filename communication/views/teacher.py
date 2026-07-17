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

from accounts.models import User, StudentProfile
from accounts.permissions import IsTeacher
from communication.models import Notification, Message
from communication.serializers.teacher import TeacherNotificationSerializer
from communication.serializers.message import (
    MessageSerializer,
    ConversationContactSerializer,
)
from administration.models import Complaint


# ── BEHAVIOUR NOTIFICATION ─────────────────────────────────────────────

class TeacherBehaviourNotificationView(APIView):
    """POST /api/teacher/notify-parent/<student_id>"""
    permission_classes = [IsTeacher]

    def post(self, request, student_id):
        from academics.models import Subject
        try:
            teacher_profile = request.user.teacher_profile
            student = StudentProfile.objects.select_related("user", "class_section").get(id=student_id)

            is_teacher_of_student = Subject.objects.filter(
                assigned_teacher=teacher_profile,
                class_section=student.class_section,
            ).exists()
            if not is_teacher_of_student:
                return Response({"detail": "You are not assigned to this student's class."}, status=403)
        except StudentProfile.DoesNotExist:
            return Response({"detail": "Student not found."}, status=404)
        except Exception:
            return Response({"detail": "Teacher profile not found."}, status=403)

        message = request.data.get("message", "").strip()
        if not message:
            return Response({"detail": "message field is required."}, status=400)

        parent_profiles = student.parents.select_related("user").all()
        if not parent_profiles.exists():
            return Response({"detail": "No parent linked to this student."}, status=404)

        notifications_created = []
        for parent_profile in parent_profiles:
            notif = Notification.objects.create(
                sender=request.user,
                receiver=parent_profile.user,
                type="in_app",
                message=message,
                reference_type="student_behaviour",
                reference_id=student.id,
            )
            notifications_created.append({
                "notification_id": notif.id,
                "parent_name": parent_profile.user.full_name,
                "student_name": student.user.full_name,
                "message": message,
            })

        return Response(
            {
                "detail": f"Notification sent to {len(notifications_created)} parent(s).",
                "notifications": notifications_created,
            },
            status=201,
        )


# ── CONVERSATIONS ─────────────────────────────────────────────

class TeacherConversationListView(generics.ListAPIView):
    """GET /api/teacher/conversations"""
    serializer_class = ConversationContactSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return Message.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        ).order_by("-created_at")


class TeacherMessageThreadView(generics.ListAPIView):
    """GET /api/teacher/messages/<conversation_id>"""
    serializer_class = MessageSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        conversation_id = self.kwargs["conversation_id"]
        return Message.objects.filter(conversation_id=conversation_id).order_by("created_at")


class TeacherMarkMessageReadView(APIView):
    """POST /api/teacher/messages/<message_id>/mark-read"""
    permission_classes = [IsTeacher]

    def post(self, request, message_id):
        message = get_object_or_404(Message, id=message_id, receiver=request.user)
        message.is_read = True
        message.save()
        return Response({"detail": "Message marked as read."}, status=200)


# ── NOTIFICATIONS ─────────────────────────────────────────────

class TeacherNotificationListView(generics.ListAPIView):
    """GET /api/teacher/notifications"""
    serializer_class = TeacherNotificationSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return Notification.objects.filter(
            receiver=self.request.user
        ).order_by("-created_at")

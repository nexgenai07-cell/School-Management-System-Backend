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
from accounts.models import User, StudentProfile
from administration.models import Complaint


class TeacherBehaviourNotificationView(APIView):
    """
    POST /api/teacher/notify-parent/<student_id>

    Teacher student ke parent ko behaviour notification bhejta hai.
    Notification Notification table mein save hoti hai.
    Body: { "message": "Sara aaj class mein disruptive thi." }
    """
    permission_classes = [IsTeacher]

    def post(self, request, student_id):
        # Student verify karo — teacher ki class ka hona chahiye
        try:
            from academics.models import Subject
            teacher_profile = request.user.teacher_profile
            student = StudentProfile.objects.select_related(
                "user", "class_section"
            ).get(id=student_id)

            # Teacher sirf apni class ke student ko notify kar sakta hai
            is_teacher_of_student = Subject.objects.filter(
                assigned_teacher=teacher_profile,
                class_section=student.class_section,
            ).exists()

            if not is_teacher_of_student:
                return Response(
                    {"detail": "You are not assigned to this student's class."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except StudentProfile.DoesNotExist:
            return Response(
                {"detail": "Student not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception:
            return Response(
                {"detail": "Teacher profile not found."},
                status=status.HTTP_403_FORBIDDEN,
            )

        message = request.data.get("message", "").strip()
        if not message:
            return Response(
                {"detail": "message field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Student ke saare linked parents ko notify karo
        parent_profiles = student.parents.select_related("user").all()
        if not parent_profiles.exists():
            return Response(
                {"detail": "No parent linked to this student."},
                status=status.HTTP_404_NOT_FOUND,
            )

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
            status=status.HTTP_201_CREATED,
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
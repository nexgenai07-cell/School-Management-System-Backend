from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
<<<<<<< HEAD
=======
from django.utils import timezone

>>>>>>> nimra-fix-develop
from accounts.permissions import IsTeacher
from administration.models import Complaint, SchoolEvent, EventParticipation
from administration.serializers.teacher import (
    TeacherComplaintSerializer, TeacherEventSerializer, TeacherEventParticipationSerializer
)

<<<<<<< HEAD
class TeacherComplaintViewSet(viewsets.ReadOnlyModelViewSet):
    """Teachers can view complaints filed against them or filed by them."""
=======
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


class TeacherComplaintViewSet(viewsets.ModelViewSet):
    """Teachers can view complaints filed against them or filed by them.

    Also supports filing a complaint (POST) using the same endpoint:
    POST /api/teacher/complaints
    """
>>>>>>> nimra-fix-develop
    serializer_class = TeacherComplaintSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
<<<<<<< HEAD
        return Complaint.objects.filter(reporter=self.request.user) | Complaint.objects.filter(against_user=self.request.user)
=======
        return Complaint.objects.filter(reporter=self.request.user) | Complaint.objects.filter(
            against_user=self.request.user
        )

    def perform_create(self, serializer):
        # Ensure reporter is always the authenticated teacher.
        serializer.save(reporter=self.request.user)

    def create(self, request, *args, **kwargs):
        # Keep DRF default create, but add a clearer error for empty body.
        if not request.data or len(request.data) == 0:
            raise ValidationError({"detail": "Request body is required."})
        return super().create(request, *args, **kwargs)

>>>>>>> nimra-fix-develop


class TeacherEventViewSet(viewsets.ReadOnlyModelViewSet):
    """Teachers can view events they are involved in.

    SchoolEvent is created/edited/deleted only by Admin (via created_by_admin).
    """
    serializer_class = TeacherEventSerializer
    permission_classes = [IsAuthenticated, IsTeacher]


    def get_queryset(self):
        # SchoolEvent has no `teacher` FK; it uses `created_by_admin`.
<<<<<<< HEAD
        return SchoolEvent.objects.filter(created_by_admin=self.request.user).order_by("-event_date")
=======
        now = timezone.now()
        return (
            SchoolEvent.objects.filter(created_by_admin=self.request.user, event_date__gte=now)
            .order_by("event_date")
        )

>>>>>>> nimra-fix-develop




class TeacherEventParticipationViewSet(viewsets.ReadOnlyModelViewSet):
    """Teachers can view student participations in events they manage."""
    serializer_class = TeacherEventParticipationSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
<<<<<<< HEAD
        return EventParticipation.objects.filter(
            event__created_by_admin=self.request.user
        ).select_related("student__user", "event")
=======
        now = timezone.now()
        return (
            EventParticipation.objects.filter(
                event__created_by_admin=self.request.user,
                event__event_date__gte=now,
            )
            .select_related("student__user", "event")
            .order_by("event__event_date")
        )

>>>>>>> nimra-fix-develop

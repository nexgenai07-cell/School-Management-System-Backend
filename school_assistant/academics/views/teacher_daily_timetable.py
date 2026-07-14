from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from accounts.permissions import IsTeacher
from academics.models import Subject, Timetable
from academics.serializers.teacher import TeacherTimetableSerializer


class TeacherDailyTimetableView(generics.ListAPIView):
    """GET /api/teacher/daily-timetable?date=YYYY-MM-DD

    Teacher ke liye selected day ka timetable.

    - Subject-wise assignment based on Subject.assigned_teacher
    - Timetable filtered by: teacher=teacher_profile, day=<Mon/Tue/...>

    Contract:
    - If query param missing: uses today's date.
    """

    serializer_class = TeacherTimetableSerializer
    permission_classes = [IsTeacher]

    def get(self, request, *args, **kwargs):
        # Let DRF handle serialization; just normalize date query param here.
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        try:
            teacher_profile = self.request.user.teacher_profile
        except Exception:
            raise PermissionDenied("Teacher profile not found.")

        date_str = self.request.query_params.get("date")
        if date_str:
            try:
                target_date = timezone.datetime.fromisoformat(date_str).date()
            except Exception:
                raise ValidationError({"date": "Use ISO format: YYYY-MM-DD"})
        else:
            target_date = timezone.now().date()

        # Model Timetable.day is stored like "Mon", "Tue" ...
        weekday = target_date.strftime("%a")[:3]

        qs = (
            Timetable.objects.filter(teacher=teacher_profile, day=weekday)
            .select_related("subject", "class_section", "room")
        )

        # Security/consistency: teacher should only see subjects assigned to them
        allowed_subject_ids = set(
            Subject.objects.filter(assigned_teacher=teacher_profile).values_list("id", flat=True)
        )
        qs = [slot for slot in qs if slot.subject_id in allowed_subject_ids]

        # Sort by start_time
        qs.sort(key=lambda s: s.start_time)
        return qs


from datetime import timedelta

from django.utils import timezone
from rest_framework import viewsets, generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import StudentProfile
from accounts.permissions import IsTeacher
from academics.models import (
    Grade, Assignment, AssignmentSubmission,
    ClassSection, Subject, Timetable,
)
from attendance.models import Attendance
from communication.models import Notification
from academics.serializers.teacher import (
    TeacherGradeEntrySerializer,
    TeacherAssignmentSerializer,
    TeacherAssignmentSubmissionSerializer,
    TeacherClassSectionSerializer,
    TeacherStudentInClassSerializer,
    TeacherDashboardSerializer,
    TeacherTimetableSerializer,
)


# ── EXISTING VIEWS (mat hatao) ────────────────────────────────────────────────

class TeacherGradeViewSet(viewsets.ModelViewSet):
    """CRUD /api/teacher/grades"""
    serializer_class = TeacherGradeEntrySerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return Grade.objects.filter(teacher__user=self.request.user)

    def perform_create(self, serializer):
        teacher_profile = getattr(self.request.user, "teacher_profile", None)
        if not teacher_profile:
            raise PermissionDenied("Teacher profile is not available.")

        student = serializer.validated_data.get("student")
        subject = serializer.validated_data.get("subject")

        if not student or not subject:
            raise ValidationError({"detail": "student and subject are required."})

        if subject.assigned_teacher_id != teacher_profile.id:
            raise PermissionDenied("You are not assigned as the teacher for this subject.")

        if getattr(student, "class_section_id", None) != subject.class_section_id:
            raise PermissionDenied("You cannot enter grades for a student not in this subject's class-section.")

        serializer.save(teacher=teacher_profile)


class TeacherAssignmentViewSet(viewsets.ModelViewSet):
    """CRUD /api/teacher/assignments"""
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return Assignment.objects.filter(teacher__user=self.request.user)

    def perform_create(self, serializer):
        teacher_profile = getattr(self.request.user, "teacher_profile", None)
        if not teacher_profile:
            raise PermissionDenied("Teacher profile is not available.")

        subject = serializer.validated_data.get("subject")
        class_section = serializer.validated_data.get("class_section")

        if not subject or not class_section:
            raise ValidationError({"detail": "subject and class_section are required."})

        if subject.assigned_teacher_id != teacher_profile.id:
            raise PermissionDenied("You are not assigned as the teacher for this subject.")

        if subject.class_section_id != class_section.id:
            raise PermissionDenied("class_section does not match this subject.")

        serializer.save(teacher=teacher_profile)


class TeacherSubmissionViewSet(viewsets.ModelViewSet):
    """CRUD /api/teacher/submissions"""
    serializer_class = TeacherAssignmentSubmissionSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return AssignmentSubmission.objects.filter(
            assignment__teacher__user=self.request.user
        )


# ── NAYI 4 VIEWS ─────────────────────────────────────────────────────────────

class TeacherClassListView(APIView):
    """
    GET /api/teacher/classes
    Is teacher ko jo bhi class sections assign hain (Subject table se),
    unki list return karta hai.
    Frontend: attendance page pe class dropdown ke liye.
    """
    permission_classes = [IsTeacher]

    def get(self, request):
        try:
            teacher_profile = request.user.teacher_profile
        except Exception:
            return Response([])

        # Teacher ke subjects se linked unique class sections nikalo
        class_section_ids = (
            Subject.objects
            .filter(assigned_teacher=teacher_profile)
            .values_list("class_section_id", flat=True)
            .distinct()
        )
        classes = ClassSection.objects.filter(id__in=class_section_ids)
        serializer = TeacherClassSectionSerializer(classes, many=True)
        return Response(serializer.data)


class TeacherStudentListView(APIView):
    """
    GET /api/teacher/students?class_section_id=1
    Ek specific class ke saare students return karta hai.
    Teacher sirf apni assigned classes ke students dekh sakta hai.
    Frontend: attendance marking page pe students list ke liye.
    """
    permission_classes = [IsTeacher]

    def get(self, request):
        try:
            teacher_profile = request.user.teacher_profile
        except Exception:
            return Response({"detail": "Teacher profile not found."}, status=403)

        class_section_id = request.query_params.get("class_section_id")
        if not class_section_id:
            return Response(
                {"detail": "class_section_id query param is required. e.g. ?class_section_id=1"},
                status=400,
            )

        # Security: teacher sirf apni assigned class dekh sakta hai
        is_assigned = Subject.objects.filter(
            assigned_teacher=teacher_profile,
            class_section_id=class_section_id,
        ).exists()

        if not is_assigned:
            return Response(
                {"detail": "You are not assigned to this class section."},
                status=403,
            )

        students = (
            StudentProfile.objects
            .filter(class_section_id=class_section_id)
            .select_related("user")
            .order_by("roll_number")
        )

        data = [
            {
                "id": s.id,
                "roll_number": s.roll_number or "",
                "full_name": s.user.full_name,
            }
            for s in students
        ]
        return Response(data)


class TeacherDashboardView(APIView):
    """
    GET /api/teacher/dashboard
    Summary cards + 7-day attendance trend.

    Summary:
      - todayClasses:          aaj ke timetable slots count
      - pendingAssignments:    teacher ke active assignments jinka due_date future mein hai
      - attendancePercentage:  teacher ki saari classes ka aaj ka average
      - notificationsCount:    sirf unread notifications

    Trend:
      - Last 7 days, har din ka attendance rate (Present / total students)
        sirf us teacher ki assigned classes ka data
    """
    permission_classes = [IsTeacher]

    def get(self, request):
        try:
            teacher_profile = request.user.teacher_profile
        except Exception:
            return Response({"detail": "Teacher profile not found."}, status=403)

        today = timezone.now().date()

        # --- Summary ---

        # 1. Aaj ke classes (Timetable se)
        today_day = today.strftime("%a")[:3]  # "Mon", "Tue" etc
        today_classes = Timetable.objects.filter(
            teacher=teacher_profile,
            day=today_day,
        ).count()

        # 2. Pending assignments (due_date future mein)
        pending_assignments = Assignment.objects.filter(
            teacher=teacher_profile,
            due_date__gte=timezone.now(),
        ).count()

        # 3. Aaj ka attendance percentage (is teacher ki saari classes)
        class_section_ids = list(
            Subject.objects
            .filter(assigned_teacher=teacher_profile)
            .values_list("class_section_id", flat=True)
            .distinct()
        )

        today_records = Attendance.objects.filter(
            class_section_id__in=class_section_ids,
            date=today,
        )
        total_today = today_records.count()
        present_today = today_records.filter(status="Present").count()
        attendance_pct = round((present_today / total_today * 100), 1) if total_today else 0

        # 4. Unread notifications count
        unread_notifs = Notification.objects.filter(
            receiver=request.user,
            is_read=False,
        ).count()

        summary = {
            "todayClasses": today_classes,
            "pendingAssignments": pending_assignments,
            "attendancePercentage": attendance_pct,
            "notificationsCount": unread_notifs,
        }

        # --- 7-day trend ---
        trend = []
        for i in range(6, -1, -1):  # 6 days ago → today
            day = today - timedelta(days=i)
            day_records = Attendance.objects.filter(
                class_section_id__in=class_section_ids,
                date=day,
            )
            day_total = day_records.count()
            day_present = day_records.filter(status="Present").count()
            rate = round((day_present / day_total * 100), 1) if day_total else 0.0
            trend.append({
                "date": str(day),
                "attendanceRate": rate,
            })

        return Response({"summary": summary, "trend": trend})


class TeacherTimetableView(generics.ListAPIView):
    """
    GET /api/teacher/timetable
    Is teacher ka apna weekly schedule — sorted by day, phir start_time.
    """
    serializer_class = TeacherTimetableSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        try:
            teacher_profile = self.request.user.teacher_profile
        except Exception:
            return Timetable.objects.none()

        # Day order ke liye custom sort
        day_order = {"Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6}
        slots = list(
            Timetable.objects
            .filter(teacher=teacher_profile)
            .select_related("subject", "class_section", "room")
        )
        slots.sort(key=lambda s: (day_order.get(s.day, 7), s.start_time))
        return slots
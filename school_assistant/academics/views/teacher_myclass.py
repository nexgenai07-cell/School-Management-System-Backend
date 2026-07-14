from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError, PermissionDenied

from accounts.permissions import IsTeacher
from accounts.models import StudentProfile
from academics.models import ClassSection, Subject

from academics.serializers.teacher_myclass import (
    TeacherMyClassSerializer,
    TeacherMyClassStudentSerializer,
    TeacherMyClassResponseSerializer,
)


class TeacherMyClassView(APIView):
    """GET /api/teacher/my-class

    Purpose:
    - Return a single class-section assigned to the logged-in teacher
      (subject-wise assignment based on Subject.assigned_teacher).
    - Return its students so the teacher can mark attendance.

    Note:
    The codebase currently supports subject-wise teacher assignment via
    Subject.assigned_teacher. The response returns the first assigned
    class-section if multiple exist.
    """

    permission_classes = [IsTeacher]

    def get(self, request):
        try:
            teacher_profile = request.user.teacher_profile
        except Exception:
            raise PermissionDenied("Teacher profile not found.")

        # Assignment sources (coexistence):
        # 1) Subject-wise assignment: Subject.assigned_teacher -> class_section
        assigned_class_ids_subject = list(
            Subject.objects.filter(assigned_teacher=teacher_profile).values_list(
                "class_section_id", flat=True
            ).distinct()
        )

        # 2) Class-wise assignment: ClassSection.teacher_incharge
        assigned_class_ids_classwise = list(
            ClassSection.objects.filter(teacher_incharge=teacher_profile).values_list(
                "id", flat=True
            ).distinct()
        )

        assigned_class_ids = list(dict.fromkeys(
            assigned_class_ids_classwise + assigned_class_ids_subject
        ))

        if not assigned_class_ids:
            return Response(
                {"detail": "No class assigned to this teacher."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Spec contract: return ONE class for logged-in teacher.
        # If multiple are assigned, return deterministically the first id.
        class_id = assigned_class_ids[0]

        class_section = ClassSection.objects.select_related().filter(id=class_id).first()
        if not class_section:
            return Response(
                {"detail": "Assigned class not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


        students_qs = (
            StudentProfile.objects.filter(class_section=class_section)
            .select_related("user")
            .order_by("roll_number")
        )

        students_data = [
            {
                "id": s.id,
                "full_name": s.user.full_name,
                "roll_number": s.roll_number or "",
            }
            for s in students_qs
        ]

        payload = {
            "class": class_section,
            "students": students_data,
            "total_students": len(students_data),
        }


        # serializer returns key "class" even though internal source is class_
        # (we map it in serializer).


        # Validate/shape through serializer (safe).
        serializer = TeacherMyClassResponseSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)


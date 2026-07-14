from rest_framework import serializers
from academics.models import Grade, Assignment, AssignmentSubmission, ClassSection, Subject, Timetable


# ── EXISTING (mat hatao) ──────────────────────────────────────────────────────

class TeacherGradeEntrySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)

    class Meta:
        model = Grade
        fields = [
            "id", "student", "student_name", "subject",
            "exam_type", "obtained_marks", "total_marks", "exam_date"
        ]


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            "id", "title", "description", "due_date",
            "attachment_url", "subject", "class_section"
        ]


class TeacherAssignmentSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)

    class Meta:
        model = AssignmentSubmission
        fields = [
            "id", "assignment", "student", "student_name",
            "file_url", "submitted_at", "marks", "feedback"
        ]


# ── NAYE (4 endpoints ke liye) ────────────────────────────────────────────────

class TeacherClassSectionSerializer(serializers.ModelSerializer):
    """
    GET /api/teacher/classes
    Us teacher ke saare class sections jo unke subjects se linked hain.
    """
    class Meta:
        model = ClassSection
        fields = ["id", "class_name", "section"]


class TeacherStudentInClassSerializer(serializers.Serializer):
    """
    GET /api/teacher/students?class_section_id=1
    Ek class ke saare students — id, roll_number, full_name.
    """
    id = serializers.IntegerField()
    roll_number = serializers.CharField()
    full_name = serializers.CharField()


class TeacherDashboardSerializer(serializers.Serializer):
    """
    GET /api/teacher/dashboard
    Summary cards + 7-day attendance trend.
    """
    summary = serializers.DictField()
    trend = serializers.ListField(child=serializers.DictField())


class TeacherTimetableSerializer(serializers.ModelSerializer):
    """
    GET /api/teacher/timetable
    Teacher ka apna weekly schedule.
    """
    subject = serializers.SerializerMethodField()
    class_section = serializers.SerializerMethodField()
    room = serializers.SerializerMethodField()

    class Meta:
        model = Timetable
        fields = ["id", "day", "start_time", "end_time", "subject", "class_section", "room"]

    def get_subject(self, obj):
        return {"id": obj.subject.id, "name": obj.subject.subject_name}

    def get_class_section(self, obj):
        return {
            "id": obj.class_section.id,
            "class_name": obj.class_section.class_name,
            "section": obj.class_section.section,
        }

    def get_room(self, obj):
        if obj.room:
            return {"id": obj.room.id, "room_number": obj.room.name}
        return None
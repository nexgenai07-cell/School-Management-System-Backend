# academics/serializers/teacher.py
from rest_framework import serializers
from academics.models import Grade, Assignment, AssignmentSubmission, ClassSection, Timetable
from accounts.models import StudentProfile

class TeacherGradeEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = [
            "id", "student", "subject", "exam_type",
            "obtained_marks", "total_marks", "exam_date", "teacher"
        ]

class TeacherAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            "id", "title", "subject", "class_section", "teacher",
            "description", "due_date", "attachment_url", "created_at"
        ]

class TeacherAssignmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = [
            "id", "assignment", "student", "file_url",
            "submitted_at", "marks", "feedback"
        ]

class TeacherClassSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSection
        fields = ["id", "class_name", "section"]

class TeacherStudentInClassSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name")

    class Meta:
        model = StudentProfile
        fields = ["id", "roll_number", "full_name"]

class TeacherDashboardSerializer(serializers.Serializer):
    todayClasses = serializers.IntegerField()
    pendingAssignments = serializers.IntegerField()
    attendancePercentage = serializers.FloatField()
    notificationsCount = serializers.IntegerField()

class TeacherTimetableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timetable
        fields = ["id", "class_section", "subject", "teacher", "room", "day", "start_time", "end_time"]

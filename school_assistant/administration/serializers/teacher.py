from rest_framework import serializers
from administration.models import Complaint, SchoolEvent, EventParticipation

class TeacherComplaintSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source="reporter.full_name", read_only=True)

    class Meta:
        model = Complaint
<<<<<<< HEAD
        fields = ["id", "reporter_name", "complaint_type", "description", "status", "created_at"]
        read_only_fields = ["reporter_name", "status", "created_at"]

=======
        # Against_user is optional. Frontend can leave it empty when reporting a generic issue.
        fields = [
            "id",
            "reporter_name",
            "complaint_type",
            "description",
            "status",
            "attachment_url",
            "against_user",
            "created_at",
        ]
        read_only_fields = ["reporter_name", "status", "created_at"]

    def validate_complaint_type(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("complaint_type must be at least 2 characters.")
        return value.strip().title()

    def validate_description(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("description must be at least 10 characters.")
        return value.strip()


>>>>>>> nimra-fix-develop

class TeacherEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolEvent
        fields = ["id", "event_name", "event_date", "venue", "created_at"]
        read_only_fields = ["created_at"]


class TeacherEventParticipationSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)

    class Meta:
        model = EventParticipation
        fields = ["id", "event", "student", "student_name", "role", "position", "created_at"]
        read_only_fields = ["student_name", "created_at"]

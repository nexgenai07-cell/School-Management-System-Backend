from rest_framework import serializers

from academics.models import ClassSection


class TeacherMyClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassSection
        fields = ["id", "class_name", "section"]


class TeacherMyClassStudentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    roll_number = serializers.CharField(allow_blank=True)


class TeacherMyClassResponseSerializer(serializers.Serializer):
    """Response payload for GET /api/teacher/my-class."""

    # Contract requires key exactly: "class"
    class_ = TeacherMyClassSerializer(source="class", read_only=True)

    students = TeacherMyClassStudentSerializer(many=True)
    total_students = serializers.IntegerField()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if "class_" in data:
            data["class"] = data.pop("class_")
        return data


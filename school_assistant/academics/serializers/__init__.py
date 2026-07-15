# academics/serializers/__init__.py
from .admin import ClassSectionSerializer, SubjectSerializer, RoomSerializer, TimetableSerializer
from .student import GradeSerializer, AssignmentSerializer, AssignmentSubmissionSerializer

from .parent import ParentGradeSerializer, ParentAssignmentSubmissionSerializer
# academics/serializers/__init__.py
from .admin import ClassSectionSerializer, SubjectSerializer, RoomSerializer, TimetableSerializer
from .student import GradeSerializer, AssignmentSerializer, AssignmentSubmissionSerializer
from .parent import ParentGradeSerializer, ParentAssignmentSubmissionSerializer
from .teacher import (
    TeacherGradeEntrySerializer,
    TeacherAssignmentSerializer,
    TeacherAssignmentSubmissionSerializer,
    TeacherClassSectionSerializer,
    TeacherStudentInClassSerializer,
    TeacherDashboardSerializer,
    TeacherTimetableSerializer,
)

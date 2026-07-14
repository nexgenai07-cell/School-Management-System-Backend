from django.urls import path
from academics.views.teacher import (

    TeacherGradeViewSet,
    TeacherAssignmentViewSet,
    TeacherSubmissionViewSet,
    TeacherClassListView,
    TeacherStudentListView,
    TeacherDashboardView,
    TeacherTimetableView,
)
from academics.views.teacher_myclass import TeacherMyClassView
from academics.views.teacher_daily_timetable import TeacherDailyTimetableView


urlpatterns = [
    # ── Existing ──────────────────────────────────────────────────────────────
    path("teacher/grades", TeacherGradeViewSet.as_view({"get": "list", "post": "create"})),
    path("teacher/grades/<int:pk>", TeacherGradeViewSet.as_view(
        {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
    )),

    path("teacher/assignments", TeacherAssignmentViewSet.as_view({"get": "list", "post": "create"})),
    path("teacher/assignments/<int:pk>", TeacherAssignmentViewSet.as_view(
        {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
    )),

    path("teacher/submissions", TeacherSubmissionViewSet.as_view({"get": "list"})),
    path("teacher/submissions/<int:pk>", TeacherSubmissionViewSet.as_view(
        {"get": "retrieve", "put": "update", "patch": "partial_update"}
    )),

    # ── Nayi 4 endpoints ──────────────────────────────────────────────────────
    # Accept both with/without trailing slash
    path("teacher/classes", TeacherClassListView.as_view()),
    path("teacher/classes/", TeacherClassListView.as_view()),
    path("teacher/students", TeacherStudentListView.as_view()),
    path("teacher/students/", TeacherStudentListView.as_view()),
    path("teacher/dashboard", TeacherDashboardView.as_view()),
    path("teacher/dashboard/", TeacherDashboardView.as_view()),
    path("teacher/timetable", TeacherTimetableView.as_view()),
    path("teacher/timetable/", TeacherTimetableView.as_view()),

    # Teacher Daily Timetable
    # GET /api/teacher/daily-timetable?date=YYYY-MM-DD
    path("teacher/daily-timetable", TeacherDailyTimetableView.as_view()),
    path("teacher/daily-timetable/", TeacherDailyTimetableView.as_view()),


    # Teacher My-Class (assigned class + students)
    path("teacher/my-class", TeacherMyClassView.as_view()),
]

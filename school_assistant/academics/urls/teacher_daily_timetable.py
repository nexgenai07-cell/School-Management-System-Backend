from django.urls import path
from academics.views.teacher_daily_timetable import TeacherDailyTimetableView

urlpatterns = [
    path(
        "teacher/daily-timetable",
        TeacherDailyTimetableView.as_view(),
    ),
    path(
        "teacher/daily-timetable/",
        TeacherDailyTimetableView.as_view(),
    ),
]


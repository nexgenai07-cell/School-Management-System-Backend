from django.urls import path, include

urlpatterns = [
    path("", include("attendance.urls.admin")),
    # attendance.urls.teacher -- mark/lock attendance + file behavior logs, built by Dev B
]
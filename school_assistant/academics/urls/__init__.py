from django.urls import path, include

urlpatterns = [
    path("", include("academics.urls.admin")),
    # academics.urls.teacher -- Grades/Assignments routes, built by Dev B
]
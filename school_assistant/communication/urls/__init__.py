from django.urls import path, include

urlpatterns = [
    path("", include("communication.urls.admin")),
]
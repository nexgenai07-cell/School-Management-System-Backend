from django.urls import path
from communication.views.teacher import (
    TeacherNotificationListView,
    TeacherConversationListView,
    TeacherMessageThreadView,
    TeacherMarkMessageReadView,
)

urlpatterns = [
    # Notifications
    path("teacher/notifications", TeacherNotificationListView.as_view()),

    # Messaging
    # IMPORTANT: read/<int:message_id> pehle likhna hai <int:parent_id> se
    # warna Django "read" ko parent_id samjh leta hai
    path("teacher/messages/conversations", TeacherConversationListView.as_view()),
    path("teacher/messages/read/<int:message_id>", TeacherMarkMessageReadView.as_view()),
    path("teacher/messages/<int:parent_id>", TeacherMessageThreadView.as_view()),
]
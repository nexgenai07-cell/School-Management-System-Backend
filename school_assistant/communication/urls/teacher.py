from django.urls import path
<<<<<<< HEAD
from communication.views.teacher import TeacherNotificationListView

urlpatterns = [
    path("teacher/notifications", TeacherNotificationListView.as_view()),
]
=======
from communication.views.teacher import (
    TeacherNotificationListView,
    TeacherConversationListView,
    TeacherMessageThreadView,
    TeacherMarkMessageReadView,
    TeacherBehaviourNotificationView,  # ← yeh add karo
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
    path("teacher/notify-parent/<int:student_id>", TeacherBehaviourNotificationView.as_view()),  # ← yeh add karo
]
>>>>>>> nimra-fix-develop

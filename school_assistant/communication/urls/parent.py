from django.urls import path
<<<<<<< HEAD
from communication.views.parent import ParentNotificationListView

urlpatterns = [
    path("parent/notifications", ParentNotificationListView.as_view()),
]
=======
from communication.views.parent import (
    ParentNotificationListView,
    ParentConversationListView,
    ParentMessageThreadView,
    ParentMarkMessageReadView,
)

urlpatterns = [
    # Notifications
    path("parent/notifications", ParentNotificationListView.as_view()),

    # Messaging
    path("parent/messages/conversations", ParentConversationListView.as_view()),
    path("parent/messages/read/<int:message_id>", ParentMarkMessageReadView.as_view()),
    path("parent/messages/<int:teacher_id>", ParentMessageThreadView.as_view()),
]
>>>>>>> nimra-fix-develop

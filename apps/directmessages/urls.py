from django.urls import path

from apps.directmessages.views.conversation_create_views import ConversationView
from apps.directmessages.views.conversation_list_views import ConversationListView
from apps.directmessages.views.message_list_views import MessageListView

app_name = "directmessages"

urlpatterns = [
    path("conversations/", ConversationView.as_view(), name="conversations"),
    path("conversations/list/", ConversationListView.as_view(), name="conversation-list"),
    path(
        "conversations/<str:conversation_id>/messages/",
        MessageListView.as_view(),
        name="message-list",
    ),
]

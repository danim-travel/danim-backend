from django.urls import path

from apps.follows.views import FollowCreateView

app_name = "follows"

urlpatterns = [
    path("<str:user_id>", FollowCreateView.as_view(), name="follow"),
]

from django.urls import path

from .views import FeedbackView

app_name = "ai"

urlpatterns = [
    path("feedback/", FeedbackView.as_view(), name="feedback"),
]

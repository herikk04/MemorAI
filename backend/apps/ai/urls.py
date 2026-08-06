from django.urls import path

from .views import FeedbackView, SearchView

app_name = "ai"

urlpatterns = [
    path("feedback/", FeedbackView.as_view(), name="feedback"),
    path("search/", SearchView.as_view(), name="search"),
]

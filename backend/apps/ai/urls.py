from django.urls import path

from .views import FeedbackView, ReportView, SearchView, SuggestionView, TaskResultView

app_name = "ai"

urlpatterns = [
    path("feedback/", FeedbackView.as_view(), name="feedback"),
    path("search/", SearchView.as_view(), name="search"),
    path("report/", ReportView.as_view(), name="report"),
    path("suggestions/", SuggestionView.as_view(), name="suggestions"),
    path("tasks/<str:task_id>/", TaskResultView.as_view(), name="task_result"),
]

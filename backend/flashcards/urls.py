from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import CardViewSet, DashboardView, DeckViewSet

router = DefaultRouter()
router.register(r"decks", DeckViewSet, basename="deck")
router.register(r"cards", CardViewSet, basename="card")

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("", include(router.urls)),
]

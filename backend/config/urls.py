"""Central URL dispatcher, including AI apps.

Routing convention (SDD 5.1): /api/v1/<resource>/ flat across app-level
urls.py modules. Keeping a central router lets new apps register here
without editing the project package urls.py.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/", include("flashcards.urls")),
    path("api/v1/ai/", include("apps.ai.urls")),
]

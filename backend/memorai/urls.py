"""Project URL conf: delegates to config/urls.py (SDD 5.1).

Kept thin so the central router lives under backend/config/ as documented
in the SDD; this avoids spreading URL registering knowledge across the
project package.
"""
from django.urls import include, path

urlpatterns = [
    path("", include("config.urls")),
]

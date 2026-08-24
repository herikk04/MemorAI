"""
ASGI config for memorai project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import sys

# Make backend/apps/ importable as a top-level namespace.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS_DIR = os.path.join(BACKEND_DIR, "apps")
if APPS_DIR not in sys.path:
    sys.path.insert(0, APPS_DIR)

from django.core.asgi import get_asgi_application  # noqa: E402

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'memorai.settings.dev')

application = get_asgi_application()

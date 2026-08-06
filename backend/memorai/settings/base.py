"""
Base settings for MemorAI. Environment-specific settings inherit from this.
Secrets must come from env via django-environ; never hardcode keys here.
"""
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
    DATABASE_URL=(str, ""),
    REDIS_URL=(str, ""),
    CELERY_BROKER_URL=(str, ""),
    CELERY_RESULT_BACKEND=(str, ""),
)

# Read .env from backend root
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-insecure-key-change-in-prod")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "flashcards",
    "apps.ai",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "memorai.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "memorai.wsgi.application"

# Database: default to SQLite in dev; DATABASE_URL overrides for prod
if env("DATABASE_URL"):
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Register pgvector app only when running against PostgreSQL. On SQLite
# (the dev default and the test DB, both via in-memory SQLite) pgvector's
# VectorField would error at migration time; we fall back to a JSON-backed
# plain list there via _vector_field_cls() in apps.ai.models so the same
# code path works on both DBs.
if DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
    INSTALLED_APPS.append("pgvector.django")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")

# REST framework
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# AI configuration (consumed by apps.ai from Sprint 2)
AI_CONFIG = {
    "provider": env("LLM_PROVIDER", default="openai"),
    "default_model": env("LLM_DEFAULT_MODEL", default="gpt-4o-mini"),
    "timeout_seconds": env.int("LLM_TIMEOUT_SECONDS", default=30),
    "max_tokens": env.int("LLM_MAX_TOKENS", default=1024),
    "embedding_model": env("EMBEDDING_MODEL", default="text-embedding-3-small"),
    "embedding_dim": env.int("EMBEDDING_DIM", default=1536),
    "daily_token_cap_per_user": env.int("AI_DAILY_TOKEN_CAP_PER_USER", default=200000),
    "daily_cost_cap_usd": env.float("AI_DAILY_COST_CAP_USD", default=10.0),
    # Provider keys (read lazily; never logged). Defaults empty so the factory
    # picks MockLLMClient when nothing is configured (dev/test safe fallback).
    "openai_api_key": env("OPENAI_API_KEY", default=""),
    "anthropic_api_key": env("ANTHROPIC_API_KEY", default=""),
    "azure_openai_endpoint": env("AZURE_OPENAI_ENDPOINT", default=""),
    "azure_openai_api_key": env("AZURE_OPENAI_API_KEY", default=""),
    "ollama_base_url": env("OLLAMA_BASE_URL", default=""),
}

# Cache (Redis if available, else local memory)
if env("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": env("REDIS_URL"),
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "memorai-dev",
        }
    }

# Celery
if env("CELERY_BROKER_URL"):
    CELERY_BROKER_URL = env("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")
    CELERY_TASK_ALWAYS_EAGER = False
else:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True


# Logging: apps.ai logs at INFO without leaking API keys. The default handler
# does not print full prompt payloads (only flow names and metadata). DEBUG
# is only on in dev (see dev.py); prod keeps it at INFO or higher.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "loggers": {
        "apps.ai": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "flashcards": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

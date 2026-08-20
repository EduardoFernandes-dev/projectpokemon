"""Django settings for config, configuração por ambiente (.env).

Ver .env.example para a lista de variáveis suportadas. Nenhum segredo vive
neste ficheiro (ProjectPokemon-Seguranca §6).
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carregar variáveis do ficheiro .env (backend/.env), nunca commitado.
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    raw = os.environ.get(name)
    if raw is None:
        return list(default or [])
    return [item.strip() for item in raw.split(",") if item.strip()]


# ── Segurança base ──────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY em falta, define no .env (ver .env.example).")

DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1"])

# CORS, restrito por omissão (ver ProjectPokemon-Seguranca §4)
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", ["http://localhost:5173"])
CORS_ALLOW_ALL_ORIGINS = False

# ── PokeAPI (ProjectPokemon-Dados §4) ───────────────────────────────────────
POKEAPI_BASE_URL = os.environ.get("POKEAPI_BASE_URL", "https://pokeapi.co/api/v2").rstrip("/")
# TTL padrão para recursos estáticos (7 dias); a lista completa usa TTL próprio.
POKEAPI_CACHE_TTL = int(os.environ.get("POKEAPI_CACHE_TTL", str(7 * 24 * 3600)))
POKEAPI_LIST_CACHE_TTL = int(os.environ.get("POKEAPI_LIST_CACHE_TTL", str(30 * 24 * 3600)))

# True durante a suíte de testes (pytest-django), usado para desligar
# comportamentos com efeitos externos (ex.: warm-up de cache no arranque).
TESTING = os.environ.get("DJANGO_TESTING") == "1"

# ── Cache ───────────────────────────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": os.environ.get("CACHE_BACKEND", "django.core.cache.backends.locmem.LocMemCache"),
        "LOCATION": os.environ.get("CACHE_LOCATION", "pokedex-cache"),
        # Moves são cacheados por URL (/move/{id}), ~900 entradas; o default
        # de 300 entradas do LocMemCache evictaria moves a cada página.
        "OPTIONS": {
            "MAX_ENTRIES": int(os.environ.get("CACHE_MAX_ENTRIES", "5000")),
        },
    }
}

# ── DRF (ProjectPokemon-Seguranca §3) ───────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.environ.get("DJANGO_THROTTLE_RATE", "120/min"),
    },
}

# ── Application definition ──────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    "rest_framework",
    "corsheaders",
    # local
    "pokemon",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

# Database, SQLite em dev (PostgreSQL em produção: fase 6)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

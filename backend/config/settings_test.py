"""Settings de teste, herdam do dev e relaxam throttling para testes estáveis.

Usado via DJANGO_SETTINGS_MODULE (ver [tool.pytest.ini_options] no pyproject).
"""

from .settings import *  # noqa: F401,F403

DEBUG = False

# Desliga o warm-up de cache no arranque (apps.py ready()) durante os testes.
TESTING = True

REST_FRAMEWORK = REST_FRAMEWORK.copy()  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {"anon": "100000/min"}

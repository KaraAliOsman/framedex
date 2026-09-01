"""Minimal Django settings for the SHOT-01 bootstrap."""

SECRET_KEY = "shot-01-test-only"
DEBUG = False
ALLOWED_HOSTS: list[str] = []

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

INSTALLED_APPS: list[str] = []
MIDDLEWARE: list[str] = []

USE_TZ = True

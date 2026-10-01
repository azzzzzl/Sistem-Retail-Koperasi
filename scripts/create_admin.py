import os
import sys

import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("ADMIN_PASSWORD", "Admin12345")
django.setup()

from database.mongodb import ensure_indexes
from apps.authentication.services import AuthenticationService

ensure_indexes()
service = AuthenticationService()
username = os.getenv("ADMIN_USERNAME", "admin")
email = os.getenv("ADMIN_EMAIL", "admin@koperasi.local")
password = os.getenv("ADMIN_PASSWORD", "Admin12345")

try:
    service.create_user(
        username=username,
        name="Administrator Koperasi",
        email=email,
        password=password,
        role="Admin",
    )
    print(f"Admin '{username}' berhasil dibuat.")
except ValueError as exc:
    print(f"Admin belum dibuat: {exc}")

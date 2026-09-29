import os
import sys

import django


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()


from apps.authentication.services import AuthenticationService


service = AuthenticationService()

service.create_user(
    username="manager",
    name="Kasir Koperasi",
    email="kasir@koperasi.local",
    password="Kasir123",
    role="manager",
)
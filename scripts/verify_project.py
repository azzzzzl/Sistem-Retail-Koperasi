"""Lightweight project verification for local setup.

Run from the project root after installing requirements:
    python scripts/verify_project.py
"""
from __future__ import annotations

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    import django
    django.setup()
    from django.core.management import call_command
except Exception as exc:
    print(f"Django belum siap: {exc}")
    raise SystemExit(1)

try:
    call_command("check")
except Exception as exc:
    print(f"Project check gagal: {exc}")
    raise SystemExit(1)

try:
    from database.mongodb import ensure_indexes
    ok = ensure_indexes()
    print("MongoDB indexes:", "OK" if ok else "tidak semua index dapat dibuat (cek koneksi/data lama).")
except Exception as exc:
    print(f"MongoDB check dilewati/gagal: {exc}")

print("Project verification selesai.")

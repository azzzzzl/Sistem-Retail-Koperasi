import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"))
from database.mongodb import ensure_indexes

ok = ensure_indexes()
print("MongoDB index bootstrap:", "OK" if ok else "SEBAGIAN/TIDAK TERSEDIA")

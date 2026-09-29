from datetime import datetime, timezone

from django.contrib.auth.hashers import make_password, check_password

from .repositories import UserRepository
from .constants import ROLES


class AuthenticationService:

    def __init__(self):
        self.user_repository = UserRepository()

    def hash_password(self, password):
        return make_password(password)

    def verify_password(self, password, password_hash):
        return check_password(password, password_hash)

    def create_user_data(
        self,
        username,
        name,
        email,
        password,
        role="Anggota",
    ):
        if role not in ROLES:
            raise ValueError("Role tidak valid.")

        now = datetime.now(timezone.utc)

        password_hash = self.hash_password(password)

        return {
            "username": username,
            "name": name,
            "email": email,
            "passwordHash": password_hash,
            "role": role,
            "status": "active",
            "createdAt": now,
            "updatedAt": now,
        }

    def create_user(
        self,
        username,
        name,
        email,
        password,
        role="Anggota",
    ):
        existing_user = self.user_repository.find_by_username(username)

        if existing_user:
            raise ValueError("Username sudah digunakan.")

        user_data = self.create_user_data(
            username=username,
            name=name,
            email=email,
            password=password,
            role=role,
        )

        return self.user_repository.create(user_data)

    def login(self, username, password):
        user = self.user_repository.find_by_username(username)

        if not user:
            return None, "Username atau password salah."

        password_hash = user.get("passwordHash")

        if not password_hash:
            return None, "Data password user tidak valid."

        if not self.verify_password(password, password_hash):
            return None, "Username atau password salah."

        if user.get("status") != "active":
            return None, "Akun tidak aktif."

        return user, None

    def change_password(self, user_id, current_password, new_password):
        user = self.user_repository.find_by_id(user_id)

        if not user:
            return False, "User tidak ditemukan."

        password_hash = user.get("passwordHash")

        if not password_hash:
            return False, "Data password user tidak valid."

        if not self.verify_password(current_password, password_hash):
            return False, "Password lama salah."

        if current_password == new_password:
            return False, "Password baru harus berbeda dari password lama."

        new_password_hash = self.hash_password(new_password)

        self.user_repository.update_password(
            user_id,
            new_password_hash
        )

        return True, None

    def update_user(self, user_id, name, email, role):
        if role not in ROLES:
            raise ValueError("Role tidak valid.")

        user = self.user_repository.find_by_id(user_id)

        if not user:
            raise ValueError("User tidak ditemukan.")

        update_data = {
            "name": name,
            "email": email,
            "role": role,
        }

        return self.user_repository.update(
            user_id,
            update_data
        )

    def update_user_status(self, user_id, status):
        if status not in ["active", "inactive"]:
            raise ValueError("Status tidak valid.")

        user = self.user_repository.find_by_id(user_id)

        if not user:
            raise ValueError("User tidak ditemukan.")

        if user.get("status") == status:
            raise ValueError(f"User sudah berstatus {status}.")

        return self.user_repository.update_status(
            user_id=user_id,
            status=status,
        )

    def reset_password(self, user_id, new_password):
        if not new_password:
            raise ValueError("Password baru wajib diisi.")

        user = self.user_repository.find_by_id(user_id)

        if not user:
            raise ValueError("User tidak ditemukan.")

        password_hash = self.hash_password(new_password)

        result = self.user_repository.update_password(
            user_id=user_id,
            password_hash=password_hash,
        )

        if not result or result.modified_count == 0:
            raise ValueError("Password gagal diperbarui.")

        return True

    def update_user_role(self, user_id, role):
        if role not in ROLES:
            raise ValueError("Role tidak valid.")

        user = self.user_repository.find_by_id(user_id)

        if not user:
            raise ValueError("User tidak ditemukan.")

        if user.get("role") == role:
            raise ValueError(f"User sudah memiliki role {role}.")

        result = self.user_repository.update_role(
            user_id=user_id,
            role=role,
        )

        if not result or result.modified_count == 0:
            raise ValueError("Role user gagal diperbarui.")

        return True
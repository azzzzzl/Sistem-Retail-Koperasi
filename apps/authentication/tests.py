from django.test import Client, TestCase

from .repositories import UserRepository
from .services import AuthenticationService


class AuthorizationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.service = AuthenticationService()
        self.repository = UserRepository()

        self.test_users = [
            {
                "username": "test_admin_authz",
                "name": "Test Admin",
                "email": "test-admin-authz@koperasi.local",
                "password": "Test12345",
                "role": "Admin",
            },
            {
                "username": "test_kasir_authz",
                "name": "Test Kasir",
                "email": "test-kasir-authz@koperasi.local",
                "password": "Test12345",
                "role": "Kasir",
            },
            {
                "username": "test_pengurus_authz",
                "name": "Test Pengurus",
                "email": "test-pengurus-authz@koperasi.local",
                "password": "Test12345",
                "role": "Pengurus",
            },
            {
                "username": "test_anggota_authz",
                "name": "Test Anggota",
                "email": "test-anggota-authz@koperasi.local",
                "password": "Test12345",
                "role": "Anggota",
            },
        ]

        for user in self.test_users:
            existing_user = self.repository.find_by_username(user["username"])

            if not existing_user:
                self.service.create_user(
                    username=user["username"],
                    name=user["name"],
                    email=user["email"],
                    password=user["password"],
                    role=user["role"],
                )

    def tearDown(self):
        for user in self.test_users:
            self.repository.collection.delete_one(
                {"username": user["username"]}
            )

    def login_as(self, username, password="Test12345"):
        response = self.client.post(
            "/login/",
            {
                "username": username,
                "password": password,
            },
        )

        self.assertEqual(response.status_code, 302)
        return response

    def test_admin_can_access_user_management(self):
        self.login_as("test_admin_authz")

        response = self.client.get("/admin-test/")

        self.assertEqual(response.status_code, 200)

    def test_non_admin_cannot_access_user_management(self):
        non_admin_users = [
            "test_kasir_authz",
            "test_pengurus_authz",
            "test_anggota_authz",
        ]

        for username in non_admin_users:
            self.client = Client()

            self.login_as(username)

            response = self.client.get("/admin-test/")

            self.assertEqual(response.status_code, 403)

    def test_admin_can_access_sales(self):
        self.login_as("test_admin_authz")

        response = self.client.get("/sales-test/")

        self.assertEqual(response.status_code, 200)

    def test_kasir_can_access_sales(self):
        self.login_as("test_kasir_authz")

        response = self.client.get("/sales-test/")

        self.assertEqual(response.status_code, 200)

    def test_pengurus_cannot_access_sales(self):
        self.login_as("test_pengurus_authz")

        response = self.client.get("/sales-test/")

        self.assertEqual(response.status_code, 403)

    def test_anggota_cannot_access_sales(self):
        self.login_as("test_anggota_authz")

        response = self.client.get("/sales-test/")

        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_procurement(self):
        self.login_as("test_admin_authz")

        response = self.client.get("/procurement-test/")

        self.assertEqual(response.status_code, 200)

    def test_pengurus_can_access_procurement(self):
        self.login_as("test_pengurus_authz")

        response = self.client.get("/procurement-test/")

        self.assertEqual(response.status_code, 200)

    def test_kasir_cannot_access_procurement(self):
        self.login_as("test_kasir_authz")

        response = self.client.get("/procurement-test/")

        self.assertEqual(response.status_code, 403)

    def test_anggota_cannot_access_procurement(self):
        self.login_as("test_anggota_authz")

        response = self.client.get("/procurement-test/")

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_access_user_management(self):
        response = self.client.get("/admin-test/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/")

    def test_unauthenticated_cannot_access_sales(self):
        response = self.client.get("/sales-test/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/login/")
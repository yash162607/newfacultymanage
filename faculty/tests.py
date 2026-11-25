from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Faculty


@override_settings(
    ADMIN_EMAIL="admin@facultymanage.com",
    ADMIN_PASSWORD="a-long-test-password",
)
class AdminLoginTests(TestCase):
    def test_configured_admin_can_login_and_logout(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "admin@facultymanage.com",
                "password": "a-long-test-password",
                "login_type": "admin",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        user = get_user_model().objects.get(
            username="admin@facultymanage.com"
        )
        self.assertTrue(user.check_password("a-long-test-password"))
        self.assertNotEqual(user.password, "a-long-test-password")
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

        self.assertRedirects(
            self.client.get(reverse("logout")),
            reverse("login"),
        )
        self.assertRedirects(
            self.client.get(reverse("dashboard")),
            reverse("login"),
        )

    def test_invalid_admin_credentials_show_required_message(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "admin@facultymanage.com",
                "password": "incorrect",
                "login_type": "admin",
            },
        )

        self.assertContains(response, "Invalid Admin ID or Password.")

    def test_existing_non_admin_account_is_not_promoted(self):
        user = get_user_model().objects.create_user(
            username="admin@facultymanage.com",
            password="existing-password",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "admin@facultymanage.com",
                "password": "a-long-test-password",
                "login_type": "admin",
            },
        )

        user.refresh_from_db()
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertContains(response, "Invalid Admin ID or Password.")

    def test_dashboard_rejects_faculty_and_legacy_admin_sessions(self):
        self.client.session["faculty_id"] = "FAC001"
        self.assertRedirects(
            self.client.get(reverse("dashboard")),
            reverse("login"),
        )

        self.client.session["admin_id"] = 1
        self.assertRedirects(
            self.client.get(reverse("dashboard")),
            reverse("login"),
        )

    def test_dashboard_rejects_regular_django_users(self):
        user = get_user_model().objects.create_user(
            username="ordinary-user",
            password="ordinary-password",
        )
        self.client.force_login(user)

        self.assertRedirects(
            self.client.get(reverse("dashboard")),
            reverse("login"),
        )

    def test_faculty_login_remains_separate_from_admin_auth(self):
        faculty = Faculty.objects.create(
            FacultyID="FAC001",
            Password=make_password("faculty-password"),
            FirstName="Test",
            LastName="Faculty",
            Gender="Other",
            DOB="2000-01-01",
            Email="faculty@example.com",
            ContactNumber="1234567890",
            Address="Test",
            Qualification="Test",
            Designation="Teacher",
            JoiningDate="2024-01-01",
            Experience=1,
            Status="Active",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": faculty.FacultyID,
                "password": "faculty-password",
                "login_type": "faculty",
            },
        )

        self.assertRedirects(response, reverse("faculty_dashboard"))
        self.assertRedirects(
            self.client.get(reverse("dashboard")),
            reverse("login"),
        )

    def test_admin_registration_is_removed(self):
        response = self.client.get(reverse("login"))

        self.assertNotContains(response, "Register Admin")
        self.assertEqual(self.client.get("/admin-register/").status_code, 404)

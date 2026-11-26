from django.test import TestCase
from django.urls import reverse

from .models import User


def make_user(username="member1", role=User.Role.MEMBER, password="StrongPass!234"):
    return User.objects.create_user(
        username=username, email=f"{username}@example.com", password=password, role=role
    )


class RegistrationTests(TestCase):
    data = {
        "username": "newuser", "first_name": "New", "last_name": "User",
        "email": "new@example.com", "password1": "Sup3rSecret!pw", "password2": "Sup3rSecret!pw",
    }

    def test_register_success_hashes_password_and_defaults_member(self):
        r = self.client.post(reverse("accounts:register"), self.data, follow=True)
        self.assertRedirects(r, reverse("accounts:login"))
        u = User.objects.get(username="newuser")
        self.assertEqual(u.role, User.Role.MEMBER)
        self.assertNotEqual(u.password, self.data["password1"])
        self.assertTrue(u.password.startswith("pbkdf2_"))
        self.assertContains(r, "Account created successfully")

    def test_cannot_self_assign_admin_role(self):
        self.client.post(reverse("accounts:register"), {**self.data, "role": "admin"})
        self.assertEqual(User.objects.get(username="newuser").role, User.Role.MEMBER)

    def test_password_mismatch(self):
        r = self.client.post(reverse("accounts:register"), {**self.data, "password2": "different"})
        self.assertEqual(User.objects.count(), 0)
        self.assertContains(r, "didn")  # "didn’t match"

    def test_invalid_email(self):
        self.client.post(reverse("accounts:register"), {**self.data, "email": "not-an-email"})
        self.assertEqual(User.objects.count(), 0)

    def test_required_fields(self):
        self.client.post(reverse("accounts:register"), {})
        self.assertEqual(User.objects.count(), 0)

    def test_duplicate_username_and_email(self):
        make_user("newuser")
        r = self.client.post(reverse("accounts:register"), {**self.data, "email": "other@example.com"})
        self.assertEqual(User.objects.count(), 1)
        r = self.client.post(reverse("accounts:register"), {**self.data, "username": "another", "email": "NEWUSER@example.com"})
        self.assertEqual(User.objects.count(), 1)
        self.assertContains(r, "already exists")


class AuthTests(TestCase):
    def test_login_invalid_shows_error(self):
        make_user()
        r = self.client.post(reverse("accounts:login"), {"username": "member1", "password": "wrong"})
        self.assertContains(r, "Invalid username or password")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_redirects_by_role(self):
        make_user("m"); make_user("a", role=User.Role.ADMIN)
        r = self.client.post(reverse("accounts:login"), {"username": "m", "password": "StrongPass!234"})
        self.assertRedirects(r, reverse("accounts:member_dashboard"))
        self.client.post(reverse("accounts:logout"))
        r = self.client.post(reverse("accounts:login"), {"username": "a", "password": "StrongPass!234"})
        self.assertRedirects(r, reverse("accounts:admin_dashboard"))

    def test_logout_ends_session(self):
        make_user(); self.client.login(username="member1", password="StrongPass!234")
        self.client.post(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post(self):
        make_user(); self.client.login(username="member1", password="StrongPass!234")
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)

    def test_protected_pages_redirect_to_login(self):
        for name in ["dashboard", "admin_dashboard", "member_dashboard", "profile", "profile_edit"]:
            url = reverse(f"accounts:{name}")
            r = self.client.get(url)
            self.assertRedirects(r, f"{reverse('accounts:login')}?next={url}", msg_prefix=name)


class RoleAccessTests(TestCase):
    def test_member_cannot_open_admin_dashboard(self):
        make_user(); self.client.login(username="member1", password="StrongPass!234")
        r = self.client.get(reverse("accounts:admin_dashboard"))
        self.assertRedirects(r, reverse("accounts:dashboard"), fetch_redirect_response=False)

    def test_admin_cannot_open_member_dashboard(self):
        make_user("boss", role=User.Role.ADMIN); self.client.login(username="boss", password="StrongPass!234")
        r = self.client.get(reverse("accounts:member_dashboard"))
        self.assertRedirects(r, reverse("accounts:dashboard"), fetch_redirect_response=False)

    def test_each_role_sees_own_dashboard(self):
        make_user("m"); make_user("a", role=User.Role.ADMIN)
        self.client.login(username="m", password="StrongPass!234")
        self.assertContains(self.client.get(reverse("accounts:member_dashboard")), "My Entries")
        self.client.logout(); self.client.login(username="a", password="StrongPass!234")
        self.assertContains(self.client.get(reverse("accounts:admin_dashboard")), "Total users")


class ProfileTests(TestCase):
    def setUp(self):
        self.u = make_user(); self.other = make_user("other")
        self.client.login(username="member1", password="StrongPass!234")

    def test_view_own_profile(self):
        self.assertContains(self.client.get(reverse("accounts:profile")), "member1@example.com")

    def test_profile_never_shows_other_users(self):
        self.assertNotContains(self.client.get(reverse("accounts:profile")), "other@example.com")

    def test_update_profile(self):
        r = self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "Ann", "last_name": "Lee", "email": "ann@example.com", "contact_number": "+63 912 345 6789"})
        self.assertRedirects(r, reverse("accounts:profile"))
        self.u.refresh_from_db()
        self.assertEqual((self.u.first_name, self.u.email), ("Ann", "ann@example.com"))

    def test_cannot_change_role_via_profile(self):
        self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "A", "last_name": "B", "email": "member1@example.com", "role": "admin"})
        self.u.refresh_from_db()
        self.assertEqual(self.u.role, User.Role.MEMBER)

    def test_duplicate_email_rejected(self):
        self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "A", "last_name": "B", "email": "other@example.com"})
        self.u.refresh_from_db()
        self.assertEqual(self.u.email, "member1@example.com")

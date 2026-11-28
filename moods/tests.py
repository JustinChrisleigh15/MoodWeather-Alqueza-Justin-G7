from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import MoodEntry

PW = "StrongPass!234"


def make_user(name="mem1", role=User.Role.MEMBER):
    return User.objects.create_user(username=name, email=f"{name}@example.com", password=PW, role=role)


def make_entry(user, days_ago=0, **kw):
    data = dict(mood=4, stress=2, energy=4, sleep_quality=4)
    data.update(kw)
    return MoodEntry.objects.create(user=user, entry_date=timezone.localdate() - timedelta(days=days_ago), **data)


def form_data(**kw):
    data = {"entry_date": timezone.localdate().isoformat(), "mood": 4, "stress": 2, "energy": 4,
            "sleep_quality": 4, "note": "ok"}
    data.update(kw)
    return data


class AccessTests(TestCase):
    def test_login_required(self):
        e = make_entry(make_user())
        for name, args in [("entry_list", []), ("entry_create", []), ("entry_detail", [e.pk]),
                           ("entry_update", [e.pk]), ("entry_delete", [e.pk])]:
            url = reverse(f"moods:{name}", args=args)
            self.assertRedirects(self.client.get(url), f"{reverse('accounts:login')}?next={url}", msg_prefix=name)

    def test_admin_cannot_create_edit_or_delete(self):
        e = make_entry(make_user())
        make_user("boss", User.Role.ADMIN); self.client.login(username="boss", password=PW)
        for name, args in [("entry_list", []), ("entry_create", []), ("entry_update", [e.pk]), ("entry_delete", [e.pk])]:
            r = self.client.get(reverse(f"moods:{name}", args=args))
            self.assertRedirects(r, reverse("accounts:dashboard"), fetch_redirect_response=False, msg_prefix=name)


class CrudTests(TestCase):
    def setUp(self):
        self.u = make_user(); self.other = make_user("other")
        self.client.login(username="mem1", password=PW)

    def test_create_links_entry_to_user(self):
        r = self.client.post(reverse("moods:entry_create"), form_data())
        e = MoodEntry.objects.get()
        self.assertEqual(e.user, self.u)
        self.assertRedirects(r, reverse("moods:entry_detail", args=[e.pk]))

    def test_list_shows_only_own_entries(self):
        make_entry(self.u, 0, note="mine"); make_entry(self.other, 0, mood=1)
        r = self.client.get(reverse("moods:entry_list"))
        self.assertEqual(len(r.context["page"].object_list), 1)

    def test_other_users_entry_is_404_for_all_actions(self):
        e = make_entry(self.other)
        for name in ["entry_detail", "entry_update", "entry_delete"]:
            self.assertEqual(self.client.get(reverse(f"moods:{name}", args=[e.pk])).status_code, 404, name)
        self.client.post(reverse("moods:entry_delete", args=[e.pk]))
        self.assertTrue(MoodEntry.objects.filter(pk=e.pk).exists())
        self.client.post(reverse("moods:entry_update", args=[e.pk]), form_data(mood=1))
        e.refresh_from_db(); self.assertEqual(e.mood, 4)

    def test_update(self):
        e = make_entry(self.u)
        r = self.client.post(reverse("moods:entry_update", args=[e.pk]), form_data(mood=1, stress=5))
        self.assertRedirects(r, reverse("moods:entry_detail", args=[e.pk]))
        e.refresh_from_db(); self.assertEqual((e.mood, e.stress), (1, 5))

    def test_delete_needs_post_then_removes(self):
        e = make_entry(self.u)
        self.client.get(reverse("moods:entry_delete", args=[e.pk]))
        self.assertTrue(MoodEntry.objects.filter(pk=e.pk).exists())
        self.client.post(reverse("moods:entry_delete", args=[e.pk]))
        self.assertFalse(MoodEntry.objects.filter(pk=e.pk).exists())


class ValidationTests(TestCase):
    def setUp(self):
        self.u = make_user(); self.client.login(username="mem1", password=PW)

    def post(self, **kw):
        return self.client.post(reverse("moods:entry_create"), form_data(**kw))

    def test_rating_out_of_range(self):
        for field in ["mood", "stress", "energy", "sleep_quality"]:
            for bad in [0, 6, "x"]:
                self.post(**{field: bad})
        self.assertEqual(MoodEntry.objects.count(), 0)

    def test_required_fields(self):
        self.client.post(reverse("moods:entry_create"), {})
        self.assertEqual(MoodEntry.objects.count(), 0)

    def test_future_date_rejected(self):
        r = self.post(entry_date=(timezone.localdate() + timedelta(days=1)).isoformat())
        self.assertContains(r, "future date"); self.assertEqual(MoodEntry.objects.count(), 0)

    def test_one_entry_per_day(self):
        self.post(); r = self.post()
        self.assertContains(r, "already have an entry"); self.assertEqual(MoodEntry.objects.count(), 1)

    def test_same_date_allowed_for_different_users(self):
        make_entry(make_user("other"))
        self.assertEqual(self.post().status_code, 302)

    def test_edit_can_keep_own_date(self):
        e = make_entry(self.u)
        r = self.client.post(reverse("moods:entry_update", args=[e.pk]), form_data(mood=2))
        self.assertEqual(r.status_code, 302)


class DashboardTests(TestCase):
    def test_member_dashboard_shows_today_and_count(self):
        u = make_user(); make_entry(u, 0); make_entry(u, 1)
        self.client.login(username="mem1", password=PW)
        r = self.client.get(reverse("accounts:member_dashboard"))
        self.assertEqual(r.context["entry_count"], 2)
        self.assertIsNotNone(r.context["today_entry"])


from .classifier import classify, mood_score  # noqa: E402


class ClassifierTests(TestCase):
    def test_score_range(self):
        self.assertEqual(mood_score(1, 5, 1, 1), 5)
        self.assertEqual(mood_score(5, 1, 5, 5), 25)

    def test_exact_thresholds(self):
        self.assertEqual(classify(5, 2, 4, 3), "sunny")           # 21
        self.assertEqual(classify(5, 3, 3, 3), "partly_cloudy")   # 10+3+3+3 = 19
        self.assertEqual(classify(4, 3, 3, 3), "partly_cloudy")   # 8+3+3+3 = 17
        self.assertEqual(classify(4, 4, 3, 3), "cloudy")          # 8+3+3+2 = 16
        self.assertEqual(classify(3, 4, 2, 2), "rainy")           # 12
        self.assertEqual(classify(2, 4, 2, 2), "rainy")           # 10
        self.assertEqual(classify(2, 5, 1, 2), "stormy")          # 4+1+2+1 = 8


class WeatherSavedTests(TestCase):
    def test_weather_computed_on_create_and_update(self):
        u = make_user()
        e = make_entry(u, mood=5, stress=1, energy=5, sleep_quality=5)
        self.assertEqual(e.weather, "sunny")
        e.mood, e.stress, e.energy, e.sleep_quality = 1, 5, 1, 1
        e.save(); e.refresh_from_db()
        self.assertEqual(e.weather, "stormy")

    def test_user_cannot_set_weather_via_form(self):
        u = make_user(); self.client.login(username="mem1", password=PW)
        self.client.post(reverse("moods:entry_create"), form_data(mood=1, stress=5, energy=1, sleep_quality=1, weather="sunny"))
        self.assertEqual(MoodEntry.objects.get().weather, "stormy")

    def test_card_shows_weather(self):
        u = make_user(); e = make_entry(u, mood=5, stress=1, energy=5, sleep_quality=5)
        self.client.login(username="mem1", password=PW)
        self.assertContains(self.client.get(reverse("moods:entry_detail", args=[e.pk])), "Sunny")

    def test_member_dashboard_shows_todays_card(self):
        u = make_user(); make_entry(u, mood=1, stress=5, energy=1, sleep_quality=1)
        self.client.login(username="mem1", password=PW)
        self.assertContains(self.client.get(reverse("accounts:member_dashboard")), "Stormy")


class AdminOverviewTests(TestCase):
    def setUp(self):
        self.m1 = make_user("alice"); self.m2 = make_user("bob")
        make_entry(self.m1, mood=5, stress=1, energy=5, sleep_quality=5)
        make_entry(self.m2, mood=1, stress=5, energy=1, sleep_quality=1)
        make_user("boss", User.Role.ADMIN)

    def test_admin_sees_all_entries_and_filters(self):
        self.client.login(username="boss", password=PW)
        r = self.client.get(reverse("moods:admin_entries"))
        self.assertEqual(len(r.context["page"].object_list), 2)
        self.assertEqual(len(self.client.get(reverse("moods:admin_entries"), {"q": "alice"}).context["page"].object_list), 1)
        self.assertEqual(len(self.client.get(reverse("moods:admin_entries"), {"weather": "stormy"}).context["page"].object_list), 1)

    def test_admin_can_view_card_but_not_edit(self):
        e = MoodEntry.objects.filter(user=self.m1).first()
        self.client.login(username="boss", password=PW)
        self.assertEqual(self.client.get(reverse("moods:entry_detail", args=[e.pk])).status_code, 200)
        r = self.client.post(reverse("moods:entry_update", args=[e.pk]), form_data(mood=1))
        self.assertEqual(r.status_code, 302)
        e.refresh_from_db(); self.assertEqual(e.mood, 5)

    def test_member_cannot_open_admin_overview(self):
        self.client.login(username="alice", password=PW)
        self.assertRedirects(self.client.get(reverse("moods:admin_entries")), reverse("accounts:dashboard"), fetch_redirect_response=False)

    def test_admin_dashboard_shows_summary(self):
        self.client.login(username="boss", password=PW)
        r = self.client.get(reverse("accounts:admin_dashboard"))
        self.assertEqual(r.context["total_entries"], 2)
        self.assertEqual(dict(r.context["weather_counts"])["Sunny"], 1)

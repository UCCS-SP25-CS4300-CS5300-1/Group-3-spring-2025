# tests.py
import json
import requests
from django.test import TestCase, Client
from django.urls import reverse
from datetime import datetime, timedelta
from django.utils.timezone import now
from home.models import Event, Module, ModuleItem, UserProfile
from home.views import get_active_courses, parse_date, fetch_assignments
from django.contrib.auth.models import User
from django.utils import timezone
from unittest.mock import patch


# Test for properly displaying academic work on calendar
class CalendarViewTests(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'testpass'
        self.user = User.objects.create_user(username=self.username, password=self.password)

        # Log in the user before testing
        self.client.login(username=self.username, password=self.password)
        self.other = User.objects.create_user(username='other', password='otherpass')

    def test_calendar_view(self):
        # Create test events
        event_1 = Event.objects.create(
            user=self.user,
            title="Math Homework 1",
            description="Complete problems 1, 2, and 3.",
            due_date=datetime(2025, 3, 15),
            event_type="assignment"
        )
        event_2 = Event.objects.create(
            user=self.user,
            title="SE Test",
            description="Use the study guide given in class to prepare for test.",
            due_date=datetime(2025, 3, 16),
            event_type="test"
        )

        response = self.client.get(reverse('calendar_view')) 
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, event_1.title)
        self.assertContains(response, event_2.title)
        self.assertContains(response, "2025-03-15")  
        self.assertContains(response, "2025-03-16")


# Test to check clear calendar GET
    def test_clear_calendar_get_request(self):
        Event.objects.create(
            user=self.user,
            title="Alice's Event",
            description="Should be deleted",
            due_date=datetime(2025,3,20),
            event_type="assignment",
        )
        Event.objects.create(
            user=self.other,
            title="Bob's Event",
            description="Should survive",
            due_date=datetime(2025,3,21),
            event_type="test",
        )

        response=self.client.post(reverse('clear_calendar'))
        self.assertRedirects(response, reverse('calendar_view'))

        # alice’s events are gone
        self.assertFalse(Event.objects.filter(user=self.user).exists())
        # bob’s are still there
        self.assertTrue(Event.objects.filter(user=self.other).exists())


# Test to check clear calendar POST
    def test_clear_calendar_post_request(self):
        Event.objects.create(
            user=self.user,
            title="User's Assignment",
            description="Belongs to testuser",
            due_date=datetime(2025, 3, 21),
            event_type="assignment",
            course_name="TestCourse"
        )
        Event.objects.create(
            user=self.other,
            title="Other's Assignment",
            description="Belongs to other",
            due_date=datetime(2025, 3, 22),
            event_type="assignment",
            course_name="OtherCourse"
        )

        response = self.client.post(reverse('clear_calendar'))
        self.assertRedirects(response, reverse('calendar_view'))

        # only self.user's events should be gone
        self.assertEqual(
            Event.objects.filter(user=self.user).count(),
            0,
            "All of the logged‑in user’s events should be deleted"
        )
        # the other user’s event should still exist
        self.assertEqual(
            Event.objects.filter(user=self.other).count(),
            1,
            "Events belonging to other users must remain"
        )


# Test to check if there is anything missing/Invalid
    def test_fetch_assignments_invalid_credentials(self):
        response = self.client.post(reverse('fetch_assignments'), {
            'canvas_url': 'https://invalid-canvas.example.com',
            'api_token': ''
        })
        self.assertEqual(response.status_code, 302)


# Test for user profiles and loggin in
class LoginTest(TestCase):
    def setUp(self):
        self.username = "usertest"
        self.password = "1234testing"
        self.user=User.objects.create_user(username=self.username,
                                            password=self.password)

    def test_login_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/login.html')

    def test_login_successful(self):
        login_data = {
            'username': self.username,
            'password': self.password
        }
        response = self.client.post(reverse('login'), data=login_data)
        self.assertRedirects(response, reverse('index'))
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_failures(self):
        login_data = {
            'username': self.username,
            'password': 'wrongpassword'
        }
        response = self.client.post(reverse('login'), data=login_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct username and password")
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_user_profile_exists_after_login(self):
        # Log in the user and verify that a userprofile exists.
        self.client.login(username=self.username, password=self.password)
        user=User.objects.get(username=self.username)
        self.assertTrue(hasattr(user, 'userprofile'))


# Utility functions tests
class UtilsTests(TestCase):
    def test_parse_date_none_and_empty(self):
        self.assertIsNone(parse_date(None))
        self.assertIsNone(parse_date(""))

    def test_parse_date_with_Z_and_without(self):
        dt1 = parse_date("2025-05-01T12:00:00Z")
        dt2 = parse_date("2025-05-01T12:00:00")
        expected = datetime(2025, 5, 1, 12, 0)
        self.assertEqual(dt1, expected)
        self.assertEqual(dt2, expected)

    def test_parse_date_invalid_string(self):
        self.assertIsNone(parse_date("not-a-date"))

    @patch('home.views.fetch_json')
    def test_get_active_courses_success(self, mock_fetch):
        mock_fetch.return_value = [{'id': 99}]
        result = get_active_courses("https://canvas.test", "tok")
        self.assertEqual(result, [{'id': 99}])
        mock_fetch.assert_called_once()

    @patch('home.views.fetch_json')
    def test_get_active_courses_failure(self, mock_fetch):
        mock_fetch.side_effect = requests.RequestException("fail")
        with self.assertRaises(Exception) as cm:
            get_active_courses("https://canvas.test", "tok")
        self.assertIn("fail", str(cm.exception))


# Carson's View functions tests
class ViewFunctionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='viewuser', password='pass')
        self.client.login(username='viewuser', password='pass')

    def test_courses_list(self):
        Module.objects.create(
            user=self.user,
            course_name="CourseX",
            title="M1",
            description="D1")
        Module.objects.create(
            user=self.user,
            course_name="CourseY",
            title="M2",
            description="D2")
        response = self.client.get(reverse('courses_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn("CourseX", response.context['courses'])
        self.assertIn("CourseY", response.context['courses'])

    def test_course_detail(self):
        Event.objects.create(
            user=self.user,
            title="A1", description="D1", 
            due_date=datetime(2025,6,1), 
            event_type="assignment", 
            course_name="C1")
        Module.objects.create(user=self.user, course_name="C1", title="Mod1", description="Desc")
        response = self.client.get(reverse('course_detail', args=["C1"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['assignments']), 1)
        self.assertEqual(len(response.context['modules']), 1)

    def test_assignment_detail(self):
        ev = Event.objects.create(
            user=self.user, 
            title="A2", 
            description="Desc2", 
            due_date=datetime(2025,7,1), 
            event_type="test", 
            course_name="C2")
        response = self.client.get(reverse('assignment_detail', args=[ev.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A2")

    def test_wipe_saved(self):
        # Creates data to wipe
        Event.objects.create(
            user=self.user, 
            title="X", 
            description="D", 
            due_date=datetime(2025,8,1), 
            event_type="assignment", 
            course_name="C3")
        Module.objects.create(user=self.user, course_name="C3", title="Mod3", description="Desc3")
        ModuleItem.objects.create(module=Module.objects.first(), title="Item3", item_type="T")
        response = self.client.post(reverse('clear_calendar'))
        response = self.client.post(reverse('wipe_saved'))
        self.assertRedirects(response, reverse('calendar_view'))
        self.assertEqual(Event.objects.filter(user=self.user).count(), 0)
        self.assertEqual(Module.objects.filter(user=self.user).count(), 0)
        self.assertEqual(
             ModuleItem.objects.filter(module__user=self.user).count(),
             0
         )


# fetch_assignments testing
class FetchAssignmentsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = self.client.login(username='user', password='pass') or None
        # ensure a user with a profile exists
        from django.contrib.auth.models import User
        u = User.objects.create_user(username='user', password='pass')
        u.userprofile  # assume signal or auto-creation
        self.client.login(username='user', password='pass')
        self.canvas_url = 'https://canvas.example.com'
        self.api_token = 'token123'

    def test_non_post_redirects(self):
        response = self.client.get(reverse('fetch_assignments'))
        self.assertRedirects(response, reverse('index'))

    @patch('home.views.get_active_courses', return_value=[])
    def test_no_courses_redirects(self, mock_courses):
        response = self.client.post(
            reverse('fetch_assignments'),
            {'canvas_url': self.canvas_url, 'api_token': self.api_token}
        )
        self.assertRedirects(response, reverse('index'))
        mock_courses.assert_called_once_with(self.canvas_url, self.api_token)

    @patch('home.views.fetch_json')
    @patch('home.views.get_active_courses')
    def test_success_creates_events_modules_and_items(self, mock_courses, mock_fetch):
        mock_courses.return_value = [{'id': 1, 'name': 'Course1'}]

        def side_effect(url, headers):
            if 'assignments?' in url:
                return [{'name': 'Assign', 'due_at': '2025-05-01T00:00:00Z', 'description': 'D'}]
            if 'modules?' in url:
                return [{'id': 10, 'name': 'ModA', 'description': 'MD'}]
            if '/items' in url:
                return [{'title': 'It1', 'type': 'Page', 'external_url': 'http://x', 'content': 'C1'}]
            return []

        mock_fetch.side_effect = side_effect

        response = self.client.post(
            reverse('fetch_assignments'),
            {'canvas_url': self.canvas_url, 'api_token': self.api_token}
        )
        self.assertRedirects(response, reverse('calendar_view'))

        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(Module.objects.count(), 1)
        self.assertEqual(ModuleItem.objects.count(), 1)

    @patch('home.views.fetch_json', side_effect=Exception("fail"))
    @patch('home.views.get_active_courses')
    def test_fetch_json_errors(self, mock_courses, mock_fetch):
        # fetch_json always throws — assignments/modules both empty, module_jobs empty
        mock_courses.return_value = [{'id': 2, 'name': 'Course2'}]

        response = self.client.post(
            reverse('fetch_assignments'),
            {'canvas_url': self.canvas_url, 'api_token': self.api_token}
        )
        self.assertRedirects(response, reverse('calendar_view'))
        self.assertEqual(Event.objects.count(), 0)
        self.assertEqual(Module.objects.count(), 0)
        self.assertEqual(ModuleItem.objects.count(), 0)

    @patch('home.views.fetch_json')
    @patch('home.views.get_active_courses')
    def test_old_assignments_filtered(self, mock_courses, mock_fetch):
        mock_courses.return_value = [{'id': 3, 'name': 'Course3'}]

        def side_effect(url, headers):
            if 'assignments?' in url:
                # outside current year → should be ignored
                return [{'name': 'Old', 'due_at': '2024-01-01T00:00:00Z', 'description': 'D'}]
            if 'modules?' in url:
                return []
            return []

        mock_fetch.side_effect = side_effect

        response = self.client.post(
            reverse('fetch_assignments'),
            {'canvas_url': self.canvas_url, 'api_token': self.api_token}
        )
        self.assertRedirects(response, reverse('calendar_view'))
        self.assertEqual(Event.objects.count(), 0)
        self.assertEqual(Module.objects.count(), 0)
        self.assertEqual(ModuleItem.objects.count(), 0)

    @patch('home.views.fetch_json')
    @patch('home.views.get_active_courses')
    def test_no_modules_creates_only_events(self, mock_courses, mock_fetch):
        mock_courses.return_value = [{'id': 4, 'name': 'Course4'}]

        def side_effect(url, headers):
            if 'assignments?' in url:
                return [{'name': 'AssignX', 'due_at': '2025-04-01T00:00:00Z', 'description': 'DX'}]
            if 'modules?' in url:
                return []
            return []

        mock_fetch.side_effect = side_effect

        response = self.client.post(
            reverse('fetch_assignments'),
            {'canvas_url': self.canvas_url, 'api_token': self.api_token}
        )
        self.assertRedirects(response, reverse('calendar_view'))
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(Module.objects.count(), 0)
        self.assertEqual(ModuleItem.objects.count(), 0)


# Test for assignment creation and displaying custom assignments properly in calendar view
class CustomAssignmentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test", password="secret123")
        Event.objects.create(
            user=self.user,
            title="placeholder",
            description="",
            due_date=datetime.now() + timedelta(days=2),
            event_type="assignment",
            course_name="Test Course"
        )
        self.client.login(username="test", password="secret123")

    def test_add_event_sets_custom_flag(self):
        url = reverse("add_event")
        due = (timezone.now() + timezone.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        data = {
            "title": "My Custom Task",
            "description": "A special one-off",
            "due_date": due,
            "event_type": "assignment",
            "course_name": "Test Course",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        ev = Event.objects.get(user=self.user, title="My Custom Task")
        self.assertTrue(ev.custom, "custom flag must be set to True for hand‑added events")
        self.assertEqual(ev.description, "A special one-off")

    def test_calendar_view_includes_custom_flag(self):
        # Test filtering calender viwed based on Event.custom boolean value
        now = timezone.now() + timezone.timedelta(days=1)
        Event.objects.create(
            user=self.user, title="Canvas Task", description="", 
            due_date=now, event_type="assignment", course_name="C1", custom=False
        )
        Event.objects.create(
            user=self.user, title="Manual Task", description="foo", 
            due_date=now, event_type="assignment", course_name="C2", custom=True
        )

        url = reverse("calendar_view")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        js = json.loads(resp.context["events_json"])

        # find custom event
        manual = next(e for e in js if e["title"].endswith("Manual Task"))
        canvas = next(e for e in js if e["title"].endswith("Canvas Task"))

        self.assertTrue(manual.get("custom", False), "Manual Task must have custom: true")
        self.assertFalse(canvas.get("custom", True), "Canvas Task must have custom: false")


# Basic tests for main page
class IndexViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.canvas_token = "123456789"
        profile.save()

        Event.objects.create(
            user=self.user,
            title="Past Assignment",
            event_type="assignment",
            due_date=now() - timedelta(days=2),
            course_name="Old Class"
        )

        Event.objects.create(
            user=self.user,
            title="Upcoming Assignment",
            event_type="assignment",
            due_date=now() + timedelta(days=3),
            course_name="New Class"
        )

    def test_no_login(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_token_is_detected(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("index"))
        self.assertContains(response, "Manage API Token")

    def test_index_upcoming_only(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("index"))

        self.assertContains(response, "Upcoming Assignment")
        self.assertNotContains(response, "Past Assignment")

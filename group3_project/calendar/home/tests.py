from django.test import TestCase, Client
from django.urls import reverse
<<<<<<< HEAD
from django.contrib.messages import get_messages
from django.http import Http404
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
import requests

from .models import Event, Module
from .views import (
    clear_calendar,
    index,
    calendar_view,
    parse_date,
    get_active_courses,
    get_assignments_for_course,
    fetch_assignments,
    get_modules_for_course,
    courses_list,
    course_detail,
    assignment_detail,
)

class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        #Creates a sample Event for testing assignment_detail and calendar_view.
        self.event = Event.objects.create(
            title="Test Assignment",
            description="Test description",
            due_date=datetime(2025, 4, 4, 12, 0),
            event_type="assignment",
            course_name="Test Course"
        )
        #Creates a sample Module for testing modules view and course_detail.
        self.module = Module.objects.create(
            course_name="Test Course",
            title="Module A",
            description="Module A Desc"
        )
    
    def test_clear_calendar_post(self):
        #Creates an extra event so that clear_calendar has something to delete.
=======
from datetime import datetime, timedelta
from home.models import Event
from django.contrib.auth.models import User

# Test for properly displaying academic work on calendar
class CalendarViewTests(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'testpass'
        self.user = User.objects.create_user(username=self.username, password=self.password)

        # Log in the user before testing
        self.client.login(username=self.username, password=self.password)

    def test_calendar_view(self):
        # Create test events
        event_1 = Event.objects.create(
            user = self.user,
            title = "Math Homework 1",
            description ="Complete problems 1, 2, and 3.",
            due_date = datetime(2025, 3, 15),
            event_type ="assignment"
        )
        event_2 = Event.objects.create(
            user = self.user,
            title = "SE Test",
            description = "Use the study guide given in class to prepare for test.",
            due_date = datetime(2025, 3, 16),
            event_type = "test"
        )

        response = self.client.get(reverse('calendar_view')) 
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, event_1.title)
        self.assertContains(response, event_2.title)
        self.assertContains(response, "2025-03-15")  
        self.assertContains(response, "2025-03-16")

#Test to check clear calendar GET
    def test_clear_calendar_get_request(self):
        #Create a test event
        event = Event.objects.create(
            title = "Test Event",
            description ="Test event description.",
            due_date = datetime(2025, 3, 20),
            event_type ="assignment"
        )
        #Perform a GET request to the clear_calendar view
        response = self.client.get(reverse('clear_calendar'))
        #Expecting a redirect 
        self.assertEqual(response.status_code, 302)
        #Ensure the event is still in the database
        self.assertEqual(Event.objects.count(), 1)

#Test to check clear calendar POST
    def test_clear_calendar_post_request(self):
        #Create test events
>>>>>>> Calender_Login
        Event.objects.create(
            title="Another Assignment",
            description="Desc",
            due_date=datetime(2025, 4, 5, 12, 0),
            event_type="assignment",
            course_name="Test Course"
        )
        response = self.client.post(reverse('clear_calendar'))
        self.assertRedirects(response, reverse('calendar_view'))
        self.assertEqual(Event.objects.count(), 0)
<<<<<<< HEAD
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("All events have been cleared." in str(msg) for msg in messages_list))
    
    def test_clear_calendar_get(self):
        response = self.client.get(reverse('clear_calendar'))
        self.assertRedirects(response, reverse('calendar_view'))
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Invalid request." in str(msg) for msg in messages_list))
    
    def test_index_view(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html')
    
    def test_calendar_view(self):
        response = self.client.get(reverse('calendar_view'))
        self.assertEqual(response.status_code, 200)
        #The view passes JSON of events in context.
        events_json = response.context['events_json']
        events = json.loads(events_json)
        self.assertEqual(len(events), Event.objects.count())
    
    def test_parse_date(self):
        valid_date = "2025-04-04T12:00:00Z"
        dt = parse_date(valid_date)
        self.assertEqual(dt, datetime.fromisoformat("2025-04-04T12:00:00"))
        self.assertIsNone(parse_date("invalid"))
        self.assertIsNone(parse_date(""))
    
    @patch('home.views.requests.get')
    def test_get_active_courses_success(self, mock_get):
        fake_response = MagicMock()
        fake_response.raise_for_status.return_value = None
        fake_response.json.return_value = [{"id": 1, "name": "Course 1"}]
        mock_get.return_value = fake_response
        courses = get_active_courses("https://canvas.example.com", "token")
        self.assertEqual(courses, [{"id": 1, "name": "Course 1"}])
    
    @patch('home.views.requests.get')
    def test_get_active_courses_failure(self, mock_get):
        mock_get.side_effect = requests.RequestException("Error")
        with self.assertRaises(Exception) as context:
            get_active_courses("https://canvas.example.com", "token")
        self.assertIn("Error fetching courses", str(context.exception))
    
    @patch('home.views.requests.get')
    def test_get_assignments_for_course_success(self, mock_get):
        fake_response = MagicMock()
        fake_response.raise_for_status.return_value = None
        fake_response.json.return_value = [{
            "name": "Assignment 1",
            "due_at": "2025-04-04T12:00:00Z",
            "description": "Desc"
        }]
        mock_get.return_value = fake_response
        assignments = get_assignments_for_course("https://canvas.example.com", 1, "token")
        self.assertEqual(assignments, [{
            "name": "Assignment 1",
            "due_at": "2025-04-04T12:00:00Z",
            "description": "Desc"
        }])
    
    @patch('home.views.requests.get')
    def test_get_assignments_for_course_failure(self, mock_get):
        mock_get.side_effect = requests.RequestException("Error")
        assignments = get_assignments_for_course("https://canvas.example.com", 1, "token")
        self.assertEqual(assignments, [])
    
    @patch('home.views.requests.get')
    def test_get_modules_for_course_success(self, mock_get):
        fake_response = MagicMock()
        fake_response.raise_for_status.return_value = None
        fake_response.json.return_value = [{"id": 10, "name": "Module 1", "description": "Mod Desc"}]
        mock_get.return_value = fake_response
        modules = get_modules_for_course("https://canvas.example.com", 1, "token")
        self.assertEqual(modules, [{"id": 10, "name": "Module 1", "description": "Mod Desc"}])
    
    @patch('home.views.requests.get')
    def test_get_modules_for_course_failure(self, mock_get):
        mock_get.side_effect = requests.RequestException("Error")
        modules = get_modules_for_course("https://canvas.example.com", 1, "token")
        self.assertEqual(modules, [])
    
    @patch('home.views.get_active_courses')
    @patch('home.views.get_assignments_for_course')
    def test_fetch_assignments(self, mock_get_assignments, mock_get_active_courses):
        #Clear existing events.
        Event.objects.all().delete()
        #Setup mocks to simulate a successful API response.
        mock_get_active_courses.return_value = [{"id": 1, "name": "Course 1"}]
        mock_get_assignments.return_value = [{
            "name": "Assignment 1",
            "due_at": "2025-04-04T12:00:00Z",
            "description": "A1 Desc"
        }]
        post_data = {"canvas_url": "https://canvas.example.com", "api_token": "token"}
        response = self.client.post(reverse('fetch_assignments'), data=post_data)
        self.assertRedirects(response, reverse('calendar_view'))
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Fetched and added" in str(msg) for msg in messages_list))
        # Only one Event should be created.
        self.assertEqual(Event.objects.count(), 1)
=======

#Test to check if there is anything missing/Invalid
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
        self.user = User.objects.create_user(username=self.username, password=self.password)

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
        user = User.objects.get(username=self.username)
        # This test assumes you have signals set up to automatically create a UserProfile.
        self.assertTrue(hasattr(user, 'userprofile'))
>>>>>>> Calender_Login

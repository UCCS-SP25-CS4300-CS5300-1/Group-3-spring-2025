from django.test import TestCase
from django.urls import reverse
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
        Event.objects.create(
            title = "Test Event 1",
            description ="Test event description 1.",
            due_date = datetime(2025, 3, 21),
            event_type ="assignment"
        )
        Event.objects.create(
            title = "Test Event 2",
            description ="Test event description 2.",
            due_date = datetime(2025, 3, 22),
            event_type ="test"
        )
        #Performs a POST request to the clear_calendar view
        response = self.client.post(reverse('clear_calendar'))
        #Checks that response is a redirect 
        self.assertEqual(response.status_code, 302)
        #Verifys that all events have been deleted
        self.assertEqual(Event.objects.count(), 0)

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
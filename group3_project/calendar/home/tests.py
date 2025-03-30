from django.test import TestCase
from django.urls import reverse
from datetime import datetime, timedelta
from .models import Event

#
class CalendarViewTests(TestCase):
    def test_calendar_view(self):

        # Create test events
        event_1 = Event.objects.create(
            title = "Math Homework 1",
            description ="Complete problems 1, 2, and 3.",
            due_date = datetime(2025, 3, 15),
            event_type ="assignment"
        )
        event_2 = Event.objects.create(
            title = "SE Test",
            description = "Use the study guide given in class to prepare for test.",
            due_date = datetime(2025, 3, 16),
            event_type = "test"
        )

        response = self.client.get(reverse('calendar_view')) 

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

#Tesr to check if there is anything missing/Invalid
    def test_fetch_assignments_invalid_credentials(self):
        response = self.client.post(reverse('fetch_assignments'), {
            'canvas_url': 'https://invalid-canvas.example.com',
            'api_token': ''
        })
        self.assertEqual(response.status_code, 302)


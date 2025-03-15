from django.test import TestCase
from django.urls import reverse
from datetime import datetime, timedelta
from home.models import Event

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

        response = self.client.get(reverse('calendar')) 

        self.assertContains(response, event_1.title)
        self.assertContains(response, event_2.title)
        self.assertContains(response, "2025-03-15")  
        self.assertContains(response, "2025-03-16")

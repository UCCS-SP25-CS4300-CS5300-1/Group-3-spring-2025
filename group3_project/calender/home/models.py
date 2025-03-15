from django.db import models

# Model for academic work including assignment, quizzes, and tests
class Event(models.Model):
    EVENT_TYPES = [

        # Event types
        ('assignment', 'Assignment'),
        ('quiz', 'Quiz'),
        ('test', 'Test'),
    ]

    title = models.CharField(max_length=255) # Name for assignment, quiz, or test
    description = models.TextField()
    due_date = models.DateTimeField()
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES)
    course_name = models.CharField(max_length=100, null=True)

    # String representation for event
    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()})"

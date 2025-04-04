# models.py
from django.db import models

#Model (for assignments, quizzes, tests)
class Event(models.Model):
    EVENT_TYPES = [
        ('assignment', 'Assignment'),
        ('quiz', 'Quiz'),
        ('test', 'Test'),
    ]
    title = models.CharField(max_length=255)  #Name for assignment, quiz, or test
    description = models.TextField()
    due_date = models.DateTimeField()
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES)
    course_name = models.CharField(max_length=100, null=True)

    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()})"


#Module model to store Canvas module information
class Module(models.Model):
    course_name = models.CharField(max_length=100)  
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)  

    def __str__(self):
        return f"{self.course_name} - {self.title}"


#Stores individual items inside the module
class ModuleItem(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=255)
    item_type = models.CharField(max_length=50, blank=True)  #e.g., "Page", "File", etc.
    file_url = models.URLField(blank=True, null=True)  #URL to a file hosted externally (Canvas)
    content = models.TextField(blank=True, null=True)  #Content field

    def __str__(self):
        return self.title


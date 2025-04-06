from django.db import models
import markdown
from taggit.managers import TaggableManager
from django.utils import timezone

class Note(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = TaggableManager(blank=True)
    
    def __str__(self):
        return self.title
    
    def get_html_content(self):
        return markdown.markdown(self.content, extensions=['extra', 'codehilite'])
    
    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super(Note, self).save(*args, **kwargs)
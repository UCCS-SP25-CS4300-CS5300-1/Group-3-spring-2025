from django.db import models
import markdown
from taggit.managers import TaggableManager
from django.utils import timezone
from django.contrib.auth.models import User


class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes', null = True)
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
    
    @property
    def filename(self):
        if self.attachment:
            return self.attachment.name.split('/')[-1]
        return None

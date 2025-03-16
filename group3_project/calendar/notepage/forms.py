from django import forms
from .models import Note

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Title'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control markdown-editor', 
                'placeholder': 'Write your notes here! Supports markdown formatting. ',
                'rows': 10
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tags (comma separated)',
                'data-role': 'tagsinput'
            }),
        }
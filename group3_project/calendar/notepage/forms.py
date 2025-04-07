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

class FileImportForm(forms.Form):
    file = forms.FileField(
        label='Select a file to import',
        help_text='Maximum file size is 5MB',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    tags = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tags (comma separated)',
            'data-role': 'tagsinput'
        })
    )
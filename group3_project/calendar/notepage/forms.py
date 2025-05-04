from django import forms
from .models import Note
import os
from django.core.exceptions import ValidationError


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
        help_text='Maximum file size is 5MB, and allowed file types are: .txt, .docx, .md',
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

    def check_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = os.path.splitext(file.name)[1].lower()

            allow_ext = ['.txt', '.docx', '.md']

            if ext not in allow_ext:
                raise ValidationError(f'Unsupported file extension. Allowed types are: {", ".join(allow_ext)}')
        return file

from datetime import datetime
from django import forms
from django.utils import timezone
from home.models import Event

class EventForm(forms.ModelForm):
    course_name = forms.ChoiceField(choices=[], required=True)

    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Due Date & Time"
    )

    class Meta:
        model = Event
        fields = ['title', 'description', 'due_date', 'event_type', 'course_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        existing = (
            Event.objects.exclude(course_name__isnull=True)
                         .exclude(course_name__exact='')
                         .values_list('course_name', flat=True)
                         .distinct()
        )
        choices = [(cn, cn) for cn in existing]
        choices.insert(0, ("", "--- Select a course ---"))
        self.fields['course_name'].choices = choices

    def clean_due_date(self):
        # Convert the naive datetime to an aware datetime in UTC
        due_date = self.cleaned_data['due_date']
    
        return timezone.make_aware(due_date, timezone.utc)
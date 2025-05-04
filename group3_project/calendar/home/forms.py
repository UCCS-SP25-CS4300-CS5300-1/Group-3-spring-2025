from django import forms
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
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            courses = (
                Event.objects.filter(user=user)
                .exclude(course_name__isnull=True)
                .exclude(course_name__exact='')
                .values_list('course_name', flat=True)
                .distinct()
            )

            choices = [(course, course) for course in courses]

            choices.insert(0, ('Personal', 'Personal'))

            choices.insert(0, ("", "--- Select a course ---"))

            self.fields['course_name'].choices = choices

        for fld in self.fields.values():
            fld.widget.attrs.update({'class': 'form-control'})

from django.shortcuts import render
from .models import Event

# Create your views here.
def index(request):
    return render(request, 'index.html')

# Function to render calendar html page
def calendar_view(request):
    # Get all events for current year
    events = Event.objects.all()

    # Render calendar html template with all events passed to it
    return render(request, 'calendar.html', {'events': events})
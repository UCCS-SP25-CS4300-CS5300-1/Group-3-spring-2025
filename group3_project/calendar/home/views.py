#views.py
from django.shortcuts import render, redirect
from django.contrib import messages
import requests
from django.http import HttpResponse
from datetime import datetime
from .models import Event
from django.shortcuts import render
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required


#Clear button view
@csrf_exempt
def clear_calendar(request):
    if request.method == "POST":
        Event.objects.all().delete()
        messages.success(request, "All events have been cleared.")
    else:
        messages.error(request, "Invalid request.")
    #Redirect back to your calendar view.
    return redirect('calendar_view')

@csrf_exempt
def index(request):
    return render(request, 'home/index.html')
    
#Calendar view
@csrf_exempt
@login_required
def calendar_view(request):
    events = list(Event.objects.filter(user=request.user).values("course_name", "title", "event_type", "due_date"))
    events_json = json.dumps(events, cls=DjangoJSONEncoder)
    return render(request, "home/calendar.html", {"events_json": events_json})

#Reuse the parse_date function Canvass Integration Script
@csrf_exempt
def parse_date(date_str):
    if not date_str:
        return None
    if date_str.endswith("Z"):
        date_str = date_str[:-1]
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None

#Gets a list of the user's active courses from Canvas.
@csrf_exempt
def get_active_courses(canvas_url, api_token):
    courses_endpoint = f"{canvas_url}/api/v1/courses?enrollment_state=active&per_page=100"
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        response = requests.get(courses_endpoint, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"Error fetching courses: {e}")
    return response.json()

#Gets all assignments for a given course.
@csrf_exempt
def get_assignments_for_course(canvas_url, course_id, api_token):
    assignments_endpoint = f"{canvas_url}/api/v1/courses/{course_id}/assignments?per_page=100"
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        response = requests.get(assignments_endpoint, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        # Log the error and return an empty list for this course.
        print(f"Error fetching assignments for course {course_id}: {e}")
        return []
    return response.json()

#The view that handles the form submission and fetches assignments.
@csrf_exempt
def fetch_assignments(request):
    if request.method == "POST":
        #Gets the credentials from the submitted form.
        canvas_url = request.POST.get('canvas_url')
        api_token = request.POST.get('api_token')

        profile = request.user.userprofile
        profile.canvas_token = api_token
        profile.save()

        try:
            courses = get_active_courses(canvas_url, api_token)
        except Exception as e:
            messages.error(request, str(e))
            return redirect('index')  

        if not courses:
            messages.error(request, "No courses found.")
            return redirect('index')

        current_year = datetime.now().year
        assignments_count = 0

        #Loop through courses and then assignments for each course.
        for course in courses:
            course_id = course.get("id")
            course_name = course.get("name", "Unknown Course")
            assignments = get_assignments_for_course(canvas_url, course_id, api_token)
            for assignment in assignments:
                assignment_name = assignment.get("name", "Untitled Assignment")
                due_at = assignment.get("due_at")
                assignment_due = parse_date(due_at) if due_at else None

                #Only add assignments with a due date in the current year.
                if assignment_due and assignment_due.year == current_year:
                    Event.objects.create(
                    user=request.user,
                    title=assignment_name,
                    description=assignment.get("description") or "",
                    due_date=assignment_due,
                    event_type="assignment",  # treating all as generic events
                    course_name=course_name
                    )
                    assignments_count += 1

        messages.success(request, f"Fetched and added {assignments_count} assignment(s) to the calendar.")
        #Redirect to the calendar view (update URL name as needed)
        return redirect('calendar_view')
    return redirect('index')

#Method to register user
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  
    else:
        form = UserCreationForm()
    return render(request, 'home/register.html', {'form': form})

@login_required
def index(request):
    return render(request, 'home/index.html')
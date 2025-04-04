#views.py
from django.shortcuts import render, redirect
from django.contrib import messages
import requests
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from datetime import datetime
from .models import Event, Module, ModuleItem
from django.shortcuts import render
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.csrf import csrf_exempt

#Clear button view
@csrf_exempt
def clear_calendar(request):
    if request.method == "POST":
        Event.objects.all().delete()
        messages.success(request, "All events have been cleared.")
    else:
        messages.error(request, "Invalid request.")
    #Redirect back to calendar view.
    return redirect('calendar_view')

@csrf_exempt
def index(request):
    return render(request, 'home/index.html')
    
#Calendar view
@csrf_exempt
def calendar_view(request):
    events = list(Event.objects.all().values("course_name", "title", "event_type", "due_date"))
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

#The view that handles the form submission and fetches assignments and modules.
@csrf_exempt
def fetch_assignments(request):
    if request.method == "POST":
        canvas_url = request.POST.get('canvas_url')
        api_token = request.POST.get('api_token')

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
        modules_count = 0

        for course in courses:
            course_id = course.get("id")
            course_name = course.get("name", "Unknown Course")
            
            #Fetch and store assignments
            assignments = get_assignments_for_course(canvas_url, course_id, api_token)
            for assignment in assignments:
                assignment_name = assignment.get("name", "Untitled Assignment")
                due_at = assignment.get("due_at")
                assignment_due = parse_date(due_at) if due_at else None

                if assignment_due and assignment_due.year == current_year:
                    Event.objects.create(
                        title=assignment_name,
                        description=assignment.get("description") or "",
                        due_date=assignment_due,
                        event_type="assignment",
                        course_name=course_name
                    )
                    assignments_count += 1
        messages.success(
            request,
            f"Fetched and added {assignments_count} assignment(s) to the calendar."
        )
        return redirect('calendar_view')
    return redirect('index')

@csrf_exempt
def get_modules_for_course(canvas_url, course_id, api_token):
    modules_endpoint = f"{canvas_url}/api/v1/courses/{course_id}/modules?per_page=100"
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        response = requests.get(modules_endpoint, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching modules for course {course_id}: {e}")
        return []
    return response.json()

#Course list view
@csrf_exempt
def courses_list(request):
    courses = Module.objects.values_list('course_name', flat=True).distinct()
    return render(request, "home/courses_list.html", {"courses": courses})

#Course details view
@csrf_exempt
def course_detail(request, course_name):
    assignments = Event.objects.filter(course_name=course_name, event_type="assignment").order_by('due_date')
    modules = Module.objects.filter(course_name=course_name)
    return render(request, "home/course_detail.html", {
        "course_name": course_name,
        "assignments": assignments,
        "modules": modules,
    })
from django.shortcuts import get_object_or_404

#Assignment Details View
@csrf_exempt
def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Event, pk=assignment_id)
    return render(request, "home/assignment_detail.html", {"assignment": assignment})


# views.py
import logging
import requests
import traceback
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.shortcuts import render, redirect
from django.contrib import messages
import requests
from django.db import transaction
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from datetime import datetime
from .models import Event, Module, ModuleItem
from django.shortcuts import render
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .forms import EventForm
from django.utils import timezone
from datetime import datetime
from django.conf import settings
from django.utils.timezone import now
import pytz


logger = logging.getLogger(__name__)

#Sets up a shared session
session = requests.Session()
adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=3)
session.mount("https://", adapter)
session.mount("http://", adapter)

#Fetches the Json data
def fetch_json(url, headers):
    resp = session.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


#Clear button view
@csrf_exempt
def clear_calendar(request):
    if request.method == "POST":
        Event.objects.filter(user=request.user).delete()
        messages.success(request, "All events have been cleared.")
    else:
        messages.error(request, "Invalid request.")
    #Redirect back to calendar view.
    return redirect('calendar_view')

@csrf_exempt
def index(request):
    return render(request, 'home/index.html')
    
#Calendar view
@login_required
def calendar_view(request):
    events = list(Event.objects.filter(user=request.user).values("course_name", "title", "description", "event_type", "due_date", "custom"))
    from django.utils.html import strip_tags
    for ev in events:
        ev["description"] = strip_tags(ev["description"] or "")
    events_json = json.dumps(events, cls=DjangoJSONEncoder)
    return render(request, "home/calendar.html", {"events_json": events_json})

#Parse's the dates for the assignments
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

#Helper to fetch all active corses
@csrf_exempt
def get_active_courses(canvas_url, api_token):
    url     = f"{canvas_url}/api/v1/courses?enrollment_state=active&per_page=100"
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        return fetch_json(url, headers)
    except Exception as e:
        raise Exception(f"Error fetching courses: {e}")

@csrf_exempt
@login_required
def fetch_assignments(request):
    if request.method != "POST":
        print("[DEBUG] fetch_assignments called with non-POST")
        return redirect('index')

    try:
        print("===== Starting fetch_assignments =====")
        canvas_url = request.POST.get('canvas_url')
        api_token  = request.POST.get('api_token')
        print(f"[DEBUG] canvas_url={canvas_url}, api_token={'*' * 4}")

        # Saves token
        profile = request.user.userprofile
        profile.canvas_token = api_token
        profile.save()
        print("[DEBUG] Saved API token to user profile")

        # Fetches courses
        courses = get_active_courses(canvas_url, api_token)
        print(f"[DEBUG] Fetched {len(courses)} active course(s)")

        if not courses:
            print("[DEBUG] No active courses found; aborting")
            return redirect('index')

        headers      = {"Authorization": f"Bearer {api_token}"}
        current_year = datetime.now().year

        # Build up all Event and Module instances
        event_objs  = []
        module_objs = []
        module_jobs = []  # stores (cid, course_name, module_id, module_title)

        for c in courses:
            cid   = c["id"]
            cname = c.get("name", "Unknown Course")

            # Fetch assignments
            try:
                assns = fetch_json(f"{canvas_url}/api/v1/courses/{cid}/assignments?per_page=100", headers)
            except Exception as e:
                print(f"[ERROR] fetching assignments for course {cid}: {e}")
                assns = []
            print(f"[DEBUG] course {cid}: {len(assns)} assignment(s)")

            for a in assns:
                due = parse_date(a.get("due_at") or "")
                if due and due.year == current_year:
                    event_objs.append(Event(
                        user=request.user,
                        title=a.get("name", "Untitled Assignment"),
                        description=a.get("description") or "",
                        due_date=due,
                        event_type="assignment",
                        course_name=cname
                    ))

            # Fetch modules
            try:
                mods = fetch_json(f"{canvas_url}/api/v1/courses/{cid}/modules?per_page=100", headers)
            except Exception as e:
                print(f"[ERROR] fetching modules for course {cid}: {e}")
                mods = []
            print(f"[DEBUG] course {cid}: {len(mods)} module(s)")

            for m in mods:
                mod_title = m.get("name", "Untitled Module")
                module_objs.append(Module(
                    user=request.user,
                    title=mod_title,
                    course_name=cname,
                    description=m.get("description") or "",
                ))
                module_jobs.append((cid, cname, m["id"], mod_title))

        print(f"[DEBUG] Prepared {len(event_objs)} Event objs")
        print(f"[DEBUG] Prepared {len(module_objs)} Module objs")

        # Bulk-inserts Events & Modules to save time
        with transaction.atomic():
            Event.objects.bulk_create(event_objs)
            print(f"[DEBUG] Inserted {len(event_objs)} Events")
            Module.objects.bulk_create(module_objs)
            print(f"[DEBUG] Inserted {len(module_objs)} Modules")

        # Sequential fetch & bulk-inserts ModuleItems to save time
        item_objs = []
        for cid, cname, mid, title in module_jobs:
            try:
                items = fetch_json(f"{canvas_url}/api/v1/courses/{cid}/modules/{mid}/items", headers)
            except Exception as e:
                print(f"[ERROR] fetching items for {cname}/{title}: {e}")
                continue

            # Fetch the Module instance we just created
            try:
                module_instance = Module.objects.get(course_name=cname, title=title)
            except Module.DoesNotExist:
                print(f"[WARN] no Module found for {cname}/{title}")
                continue

            for it in items:
                item_objs.append(ModuleItem(
                    module=module_instance,
                    title=it.get("title", "Untitled Item"),
                    item_type=it.get("type", ""),
                    file_url=it.get("external_url") or "",
                    content=it.get("content") or ""
                ))

        if item_objs:
            ModuleItem.objects.bulk_create(item_objs)
            print(f"[DEBUG] Inserted {len(item_objs)} ModuleItems")

        print("===== Finished fetch_assignments =====")
        return redirect('calendar_view')

    except Exception:
        print("===== ERROR in fetch_assignments =====")
        print(traceback.format_exc())
        return redirect('index')


#Course list view
@csrf_exempt
def courses_list(request):
    courses = Module.objects.filter(user=request.user).values_list('course_name', flat=True).distinct()
    return render(request, "home/courses_list.html", {"courses": courses})

#Course details view
@csrf_exempt
def course_detail(request, course_name):
    assignments = Event.objects.filter(course_name=course_name, event_type="assignment", user=request.user).order_by('due_date')
    modules = Module.objects.filter(course_name=course_name, user=request.user)
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

#Module wipe button
@csrf_exempt
def wipe_saved(request):
    if request.method == "POST":
        #Clears all Calendar events
        Event.objects.filter(user=request.user).delete()
        #Clears all modules
        Module.objects.filter(user=request.user).delete()
        #Clears module items
        ModuleItem.objects.filter(module__user=request.user).delete()
        messages.success(request, "All saved events and modules have been wiped.")
    else:
        messages.error(request, "Invalid request.")
    return redirect('calendar_view')

#Method to register user
@csrf_exempt
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  
    else:
        form = UserCreationForm()
    return render(request, 'home/register.html', {'form': form})

#main page
@csrf_exempt
@login_required
def index(request):
    if request.user.is_authenticated:
        profile = request.user.userprofile
        token_present = bool(profile.canvas_token)

        if token_present:
            assignment_list = Event.objects.filter(user=request.user, event_type="assignment", due_date__gte=now()).order_by('due_date')
        else:
            assignment_list = None
    else:
        token_present = False
        assignment_list = None

    return render(request, "home/index.html", {
        "token_present": token_present,
        "assignment_list": assignment_list
    })

@login_required
def add_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, user=request.user)
        if form.is_valid():
            
            event = form.save(commit=False)
            event.user = request.user  
            event.custom = True
            event.save()
        
        return redirect('calendar_view')   
    else:
        form = EventForm(user=request.user)
    return render(request, 'home/add_event.html', {'form': form})

def user_settings(request):
    profile = request.user.userprofile
    # handle deletion
    custom_events = Event.objects.filter(user=request.user, custom=True).order_by('due_date')

    if request.method == "POST":
        # if they POSTed a delete_event, handle that first:
        if request.POST.get("delete_event"):
            ev_id = request.POST["delete_event"]
            deleted, _ = Event.objects.filter(
                user=request.user,
                pk=ev_id,
                custom=True
            ).delete()
            if deleted:
                messages.success(request, "Assignment deleted.")
            else:
                messages.error(request, "Couldn’t find that assignment.")
            return redirect("user_settings")
        # handle API info update
        canvas_url = request.POST.get("canvas_url")
        canvas_token = request.POST.get("canvas_token")
        if canvas_url and canvas_token:
            profile.canvas_url = canvas_url
            profile.canvas_token = canvas_token
            profile.save()
            messages.success(request, "Canvas API information updated.")
            return redirect("user_settings")

    return render(request, "home/settings.html", {
        "custom_events": custom_events,
        "profile": profile
    })

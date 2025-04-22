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
    events = list(Event.objects.filter(user=request.user).values("course_name", "title", "event_type", "due_date", "custom"))
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

#Fetches all assignments and modules
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

        #Saves token
        profile = request.user.userprofile
        profile.canvas_token = api_token
        profile.save()
        print("[DEBUG] Saved API token to user profile")

        #Fetches courses
        courses = get_active_courses(canvas_url, api_token)
        print(f"[DEBUG] Fetched {len(courses)} active course(s)")

        if not courses:
            print("[DEBUG] No active courses found; aborting")
            return redirect('index')

        headers      = {"Authorization": f"Bearer {api_token}"}
        current_year = datetime.now().year

        #Parallel fetches assignments & modules
        assn_futs = {}
        mod_futs  = {}
        with ThreadPoolExecutor(max_workers=10) as exe:
            for c in courses:
                cid = c["id"]
                assn_url = f"{canvas_url}/api/v1/courses/{cid}/assignments?per_page=100"
                mod_url  = f"{canvas_url}/api/v1/courses/{cid}/modules?per_page=100"
                assn_futs[exe.submit(fetch_json, assn_url, headers)] = cid
                mod_futs [exe.submit(fetch_json, mod_url,  headers)] = cid

        assignments_by_course = {}
        for fut, cid in assn_futs.items():
            try:
                data = fut.result()
            except Exception as e:
                print(f"[ERROR] fetching assignments for course {cid}: {e}")
                data = []
            print(f"[DEBUG] course {cid}: {len(data)} assignment(s)")
            assignments_by_course[cid] = data

        modules_by_course = {}
        for fut, cid in mod_futs.items():
            try:
                data = fut.result()
            except Exception as e:
                print(f"[ERROR] fetching modules for course {cid}: {e}")
                data = []
            print(f"[DEBUG] course {cid}: {len(data)} module(s)")
            modules_by_course[cid] = data

        #Builds model instances
        event_objs  = []
        module_objs = []
        module_jobs = []  #stores (cid, course_name, module_id, module_title)

        for c in courses:
            cid   = c["id"]
            cname = c.get("name", "Unknown Course")

            for a in assignments_by_course.get(cid, []):
                due = parse_date(a.get("due_at") or "") 

                if due and due.year == current_year:
                    event_objs.append(Event(
                        user=request.user,
                        title=a.get("name","Untitled Assignment"),
                        description=a.get("description") or "",
                        due_date=due,
                        event_type="assignment",
                        course_name=cname
                    ))

            for m in modules_by_course.get(cid, []):
                mod_title = m.get("name","Untitled Module")
                module_objs.append(Module(
                    title=mod_title,
                    course_name=cname,
                    user=request.user,
                    description=m.get("description") or "",
                ))
                module_jobs.append((cid, cname, m["id"], mod_title))

        print(f"[DEBUG] Prepared {len(event_objs)} Event objs")
        print(f"[DEBUG] Prepared {len(module_objs)} Module objs")

        #Bulk-inserts Events & Modules to save time
        with transaction.atomic():
            Event.objects.bulk_create(event_objs)
            print(f"[DEBUG] Inserted {len(event_objs)} Events")
            Module.objects.bulk_create(module_objs)
            print(f"[DEBUG] Inserted {len(module_objs)} Modules")

        #Parallel fetch & bulk-inserts ModuleItems to save time
        item_futs = {}
        with ThreadPoolExecutor(max_workers=20) as exe:
            for cid, cname, mid, title in module_jobs:
                url = f"{canvas_url}/api/v1/courses/{cid}/modules/{mid}/items"
                item_futs[exe.submit(fetch_json, url, headers)] = (cname, title)

        #map (course_name, title) → Module instance
        unique_pairs = {(cname, title) for _, cname, _, title in module_jobs}
        saved_modules = Module.objects.filter(
            course_name__in=[p[0] for p in unique_pairs],
            title__in=[p[1] for p in unique_pairs]
        )
        mod_map = {(m.course_name, m.title): m for m in saved_modules}

        item_objs = []
        for fut, (cname, title) in item_futs.items():
            try:
                items = fut.result()
            except Exception as e:
                print(f"[ERROR] fetching items for {cname}/{title}: {e}")
                continue
            module_instance = mod_map.get((cname, title))
            if not module_instance:
                print(f"[WARN] no Module found for {cname}/{title}")
                continue
            for it in items:
                item_objs.append(ModuleItem(
                    module=module_instance,
                    title=it.get("title","Untitled Item"),
                    item_type=it.get("type",""),
                    file_url=it.get("external_url") or "",
                    content=it.get("content") or ""
                ))

        if item_objs:
            ModuleItem.objects.bulk_create(item_objs)
            print(f"[DEBUG] Inserted {len(item_objs)} ModuleItems")

        print("===== Finished fetch_assignments =====")
        return redirect('calendar_view')

    except Exception as e:
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

@csrf_exempt
@login_required
def index(request):
    return render(request, 'home/index.html')

@login_required
def add_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            
            event = form.save(commit=False)
            event.user = request.user  
            event.custom = True
            event.save()
        
        return redirect('calendar_view')   
    else:
        form = EventForm()
    return render(request, 'home/add_event.html', {'form': form})

def user_settings(request):
    return render(request, "home/settings.html")
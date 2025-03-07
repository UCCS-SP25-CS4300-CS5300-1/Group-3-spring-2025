#!/usr/bin/env python3
import requests
import sys

#Known Colleges
def get_canvas_url():
    known_colleges = {
        "harvard": "https://canvas.harvard.edu",
        "stanford": "https://canvas.stanford.edu",
        "uw": "https://canvas.uw.edu",
        "mit": "https://canvas.mit.edu",
        "umich": "https://canvas.umich.edu",
        "uccs": "http://canvas.uccs.edu"
    }
    
    #Checks if typed in college matches any
    college = input("Enter your college name: ").strip().lower()
    if college in known_colleges:
        canvas_url = known_colleges[college]
    else:
        print("College not recognized in our list.")
        domain = input("Enter your college's Canvas domain (e.g., yourcollege.instructure.com): ").strip()
        canvas_url = f"https://{domain}"
    
    return canvas_url

#Gets the Api token from the user
def get_api_token():
    #Prompts the user for the API token.
    filler = input("Enter your Canvas API token: ").strip()
    token = input("")
    if not token:
        print("No token provided. Exiting.")
        sys.exit(1)
    return token

#Gets all active courses
def get_active_courses(canvas_url, api_token):
    courses_endpoint = f"{canvas_url}/api/v1/courses?enrollment_state=active&per_page=100"
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        response = requests.get(courses_endpoint, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Error fetching courses:", e)
        sys.exit(1)
    return response.json()
#Gets all assignments from a course
def get_assignments_for_course(canvas_url, course_id, api_token):
    assignments_endpoint = f"{canvas_url}/api/v1/courses/{course_id}/assignments?per_page=100"
    headers = {"Authorization": f"Bearer {api_token}"}
    try:
        response = requests.get(assignments_endpoint, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching assignments for course {course_id}:", e)
        return []
    return response.json()

def main():    
    canvas_url = get_canvas_url()
    print(f"Using Canvas URL: {canvas_url}")
    
    api_token = get_api_token()
    
    courses = get_active_courses(canvas_url, api_token)
    if not courses:
        print("No courses found.")
        sys.exit(0)
    
    for course in courses:
        course_id = course.get("id")
        course_name = course.get("name", "Unknown Course")
        print(f"\nAssignments for {course_name} (Course ID: {course_id}):")
        
        assignments = get_assignments_for_course(canvas_url, course_id, api_token)
        if not assignments:
            print("  No assignments found.")
        else:
            for assignment in assignments:
                assignment_name = assignment.get("name", "Untitled Assignment")
                due_at = assignment.get("due_at")
                if due_at:
                    print(f"  {assignment_name} (Due: {due_at})")
                else:
                    print(f"  {assignment_name}")
        print("-" * 40)

if __name__ == "__main__":
    main()

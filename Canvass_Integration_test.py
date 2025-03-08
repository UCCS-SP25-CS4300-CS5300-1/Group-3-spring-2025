#!/usr/bin/env python3
import requests
import sys
from datetime import datetime

#Parses the dates of the assignments
def parse_date(date_str):
    """Parses an ISO8601 date string into a datetime object."""
    if not date_str:
        return None
    #Removes trailing 'Z'
    if date_str.endswith("Z"):
        date_str = date_str[:-1]
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None

#Chooses which Canvass URL to search through
def get_canvas_url():
    known_colleges = {
        "harvard": "https://canvas.harvard.edu",
        "stanford": "https://canvas.stanford.edu",
        "uw": "https://canvas.uw.edu",
        "mit": "https://canvas.mit.edu",
        "umich": "https://canvas.umich.edu",
        "uccs": "http://canvas.uccs.edu"
    }
    
    college = input("Enter your college name: ").strip().lower()
    
    #If college chosen is known
    if college in known_colleges:
        canvas_url = known_colleges[college]
    
    #Enter their own URL if its not reconized
    else:
        print("College not recognized in our list.")
        domain = input("Enter your college's Canvas domain(e.g., http://canvas.YOURCOLLEGE.edu): ").strip()
        canvas_url = f"https://{domain}"
    
    return canvas_url

#Gets the User's API Token
def get_api_token():
    token = input("Enter your Canvas API token: ").strip()
    if not token:
        print("No token provided. Exiting.")
        sys.exit(1)
    return token

#Gets a list of the user's active courses
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

#Gets all assignments for the active courses
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
    
    #If there are no courses found
    if not courses:
        print("No courses found.")
        sys.exit(0)
    
    current_year = datetime.now().year

    #List for all assignments and their descriptions
    assignments_info = []  

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
                assignment_due = parse_date(due_at) if due_at else None
                
                #Only include assignments that have a due date in the current year.
                if assignment_due and assignment_due.year == current_year:
                    print(f"  {assignment_name} (Due: {due_at})")
                    assignments_info.append({
                        "course_name": course_name,
                        "assignment_name": assignment_name,
                        "due_at": due_at,
                        "description": assignment.get("description", "")
                    })
        print("-" * 40)
    
    #Prints the stored assignments list
    print("\nStored Assignments from the current year:")
    for info in assignments_info:
        print(f"Course: {info['course_name']} | Assignment: {info['assignment_name']} | Due: {info['due_at']}")
        print(f"Description: {info['description']}\n")

if __name__ == "__main__":
    main()



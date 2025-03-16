import sys
import pytest
from datetime import datetime
import requests
from Canvass_Integration import parse_date, get_canvas_url, get_api_token, get_active_courses, get_assignments_for_course


#Tests for parse_date
def test_parse_date_valid():
    #ISO8601 with trailing "Z"
    date_str = "2023-10-05T12:34:56Z"
    result = parse_date(date_str)
    assert isinstance(result, datetime)
    assert result.year == 2023
    assert result.month == 10
    assert result.day == 5

def test_parse_date_invalid():
    #Invalid date string should return None
    assert parse_date("invalid-date") is None

def test_parse_date_empty():
    #Empty string should return None
    assert parse_date("") is None

#Tests for get_canvas_url

def test_get_canvas_url_known(monkeypatch):
    #Simulates entering a known college ("uccs")
    inputs = iter(["uccs"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    url = get_canvas_url()
    assert url == "https://canvas.uccs.edu"

def test_get_canvas_url_unknown(monkeypatch):
    #Simulates an unknown college then providing a domain
    inputs = iter(["unknowncollege", "canvas.example.com"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    url = get_canvas_url()
    assert url == "https://canvas.example.com"

#Tests for get_api_token
def test_get_api_token_valid(monkeypatch):
    inputs = iter(["validtoken"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    token = get_api_token()
    assert token == "validtoken"

def test_get_api_token_empty(monkeypatch):
    inputs = iter([""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    with pytest.raises(SystemExit):
        get_api_token()

#Helpers for simulating requests responses

class DummyResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError("HTTP Error")

def dummy_requests_get_success(url, headers):
    #Return dummy data based on the URL pattern.
    if "courses?" in url:
        return DummyResponse([{"id": 1, "name": "Test Course"}])
    elif "assignments?" in url:
        return DummyResponse([{
            "id": 101,
            "name": "Assignment 1",
            "due_at": "2023-10-10T12:00:00Z",
            "description": "Test description"
        }])
    return DummyResponse({})

def dummy_requests_get_failure(url, headers):
    raise requests.RequestException("Network error")

#Tests for get_active_courses

def test_get_active_courses_success(monkeypatch):
    monkeypatch.setattr(requests, "get", dummy_requests_get_success)
    courses = get_active_courses("https://canvas.test.edu", "token")
    assert isinstance(courses, list)
    assert len(courses) > 0
    assert courses[0]["name"] == "Test Course"

def test_get_active_courses_failure(monkeypatch):
    monkeypatch.setattr(requests, "get", dummy_requests_get_failure)
    with pytest.raises(SystemExit):
        get_active_courses("https://canvas.test.edu", "token")

#Tests for get_assignments_for_course

def test_get_assignments_for_course_success(monkeypatch):
    monkeypatch.setattr(requests, "get", dummy_requests_get_success)
    assignments = get_assignments_for_course("https://canvas.test.edu", 1, "token")
    assert isinstance(assignments, list)
    assert len(assignments) > 0
    assert assignments[0]["name"] == "Assignment 1"

def test_get_assignments_for_course_failure(monkeypatch):
    monkeypatch.setattr(requests, "get", dummy_requests_get_failure)
    assignments = get_assignments_for_course("https://canvas.test.edu", 1, "token")
    #When fetching assignments fails, the function returns an empty list instead of exiting.
    assert assignments == []




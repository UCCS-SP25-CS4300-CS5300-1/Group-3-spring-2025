from django.test import TestCase
import pytest
from django.urls import reverse
import json
from django.utils import timezone
from .models import Note
from .forms import NoteForm
import markdown

#Create a note that will be used for the other tests
@pytest.fixture
def test_note(db):
    note = Note.objects.create(
        title="Test Note",
        content="This is a test note with **markdown**"
    )
    note.tags.add("test", "django")
    return note

#Create a client to test HTTP requests
@pytest.fixture
def client_with_note(client, test_note):
    return client

#Allow access to the database
@pytest.mark.django_db
class TestNoteModel:
    def test_note_creation(self, test_note):
        assert test_note.title == "Test Note"
        assert "markdown" in test_note.content
        assert test_note.tags.count() == 2


@pytest.mark.django_db
class TestNoteForms:
    def test_valid_form(self):
        form = NoteForm(data={
            'title': 'New Note',
            'content': 'Content here',
            'tags': 'tag1, tag2'
        })
        assert form.is_valid()


@pytest.mark.django_db
class TestNoteViews:
    def test_note_list(self, client_with_note, test_note):
        response = client_with_note.get(reverse('note_list'))
        assert response.status_code == 200
        assert test_note.title in str(response.content)

    def test_note_detail(self, client_with_note, test_note):
        response = client_with_note.get(
            reverse('note_detail', args=[test_note.pk])
        )
        assert response.status_code == 200
        assert test_note.title in str(response.content)

    def test_create_note(self, client):
        response = client.post(
            reverse('create_note'),
            {
                'title': 'New Note',
                'content': 'New content',
                'tags': 'new, note'
            }
        )
        assert Note.objects.filter(title='New Note').exists()
        new_note = Note.objects.get(title='New Note')
        assert response.status_code == 302 
        assert response.url == reverse('note_detail', args=[new_note.pk])

    def test_edit_note(self, client_with_note, test_note):
        response = client_with_note.post(
            reverse('edit_note', args=[test_note.pk]),
            {
                'title': 'Updated note',
                'content': 'Updated content',
                'tags': 'updated, note'
            }
        )
        test_note.refresh_from_db()
        assert test_note.title == 'Updated note'
        assert 'updated' in test_note.tags.names()

    def test_delete_note(self, client_with_note, test_note):
        response = client_with_note.post(
            reverse('delete_note', args=[test_note.pk])
        )
        assert not Note.objects.filter(pk=test_note.pk).exists()
        assert response.url == reverse('note_list')

    def test_autosave(self, client, db):
        data = {
            'note_id': '',
            'title': 'Autosaved note',
            'content': 'Autosaved content'
        }
        response = client.post(
            reverse('autosave_note'),
            json.dumps(data),
            content_type='application/json'
        )
        response_data = json.loads(response.content)
        assert response_data['success'] == True
        assert Note.objects.filter(title='Autosaved Note').exists()

    def test_filter_by_search(self, client, db):
        Note.objects.create(title="First note", content="content1")
        Note.objects.create(title="Second note", content="content2")
        
        response = client.get(reverse('note_list') + '?search=First')
        content = str(response.content)
        assert "First note" in content
        assert "Second note" not in content
from django.test import TestCase, Client
from django.urls import reverse
import json
from .models import Note
from .forms import NoteForm

class NoteTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_note = Note.objects.create(
            title="Test note",
            content="This is a test note with **markdown**"
        )
        self.test_note.tags.add("test", "django")

    def test_note_creation(self):
        self.assertEqual(self.test_note.title, "Test note")
        self.assertIn("markdown", self.test_note.content)
        self.assertEqual(self.test_note.tags.count(), 2)

    def test_valid_form(self):
        form = NoteForm(data={
            'title': 'New note',
            'content': 'Content here',
            'tags': 'tag1, tag2'
        })
        self.assertTrue(form.is_valid())

    def test_note_list(self):
        response = self.client.get(reverse('note_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test_note.title)

    def test_note_detail(self):
        response = self.client.get(reverse('note_detail', args=[self.test_note.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test_note.title)

    def test_create_note(self):
        response = self.client.post(reverse('create_note'), {
            'title': 'New note',
            'content': 'New content',
            'tags': 'new, note'
        })
        self.assertTrue(Note.objects.filter(title='New note').exists())
        new_note = Note.objects.get(title='New note')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('note_detail', args=[new_note.pk]))

    def test_edit_note(self):
        response = self.client.post(reverse('edit_note', args=[self.test_note.pk]), {
            'title': 'Updated note',
            'content': 'Updated content',
            'tags': 'updated, note'
        })
        self.test_note.refresh_from_db()
        self.assertEqual(self.test_note.title, 'Updated note')
        self.test_note.tags.set(['updated', 'note'])
        self.assertIn('updated', self.test_note.tags.names())

    def test_delete_note(self):
        response = self.client.post(reverse('delete_note', args=[self.test_note.pk]))
        self.assertFalse(Note.objects.filter(pk=self.test_note.pk).exists())
        self.assertEqual(response.url, reverse('note_list'))

    def test_autosave(self):
        data = {
            'note_id': '',
            'title': 'Autosaved note',
            'content': 'Autosaved content'
        }
        response = self.client.post(reverse('autosave_note'), json.dumps(data), content_type='application/json')
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertTrue(Note.objects.filter(title='Autosaved note').exists())

    def test_filter_by_search(self):
        Note.objects.create(title="First note", content="content1")
        Note.objects.create(title="Second note", content="content2")
        response = self.client.get(reverse('note_list') + '?search=First')
        content = response.content.decode()
        self.assertIn("First note", content)
        self.assertNotIn("Second note", content)

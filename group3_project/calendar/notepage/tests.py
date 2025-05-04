from django.test import TestCase, Client
from django.urls import reverse
import json
from unittest.mock import patch
from .models import Note
from .forms import NoteForm
from .forms import FileImportForm
from django.core.files.uploadedfile import SimpleUploadedFile
from taggit.models import Tag
from django.contrib.auth.models import User

class NoteTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        self.test_note = Note.objects.create(
            title="Test note",
            content="This is a test note with **markdown**",
            user=self.user
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
            'tags': 'tag1,tag2'
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
            'tags': 'new,note'
        })
        self.assertTrue(Note.objects.filter(title='New note').exists())
        new_note = Note.objects.get(title='New note')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('note_detail', args=[new_note.pk]))


    def test_edit_note(self):
        response = self.client.post(reverse('edit_note', args=[self.test_note.pk]), {
            'title': 'Updated note',
            'content': 'Updated content',
            'tags': 'updated,note'
        })
        self.test_note.refresh_from_db()
        print(self.test_note.title)
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
        Note.objects.create(title="First note", content="content1", user=self.user)
        Note.objects.create(title="Second note", content="content2", user=self.user)
        response = self.client.get(reverse('note_list') + '?search=First')
        content = response.content.decode()
        self.assertIn("First note", content)
        self.assertNotIn("Second note", content)


class FileImportTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        self.test_note = Note.objects.create(
            title="Test note",
            content="This is a test note",
            user=self.user
        )
        self.test_note.tags.add("test")


    def test_import_form_valid(self):
        file = SimpleUploadedFile("test_file.txt", b"File content")
        form = FileImportForm(data={'tags': 'import,test'}, files={'file': file})
        self.assertTrue(form.is_valid())


    def test_import_form_invalid(self):
        form = FileImportForm(data={'tags': 'import,test'}) # No file is passed
        self.assertFalse(form.is_valid())


    def test_import_text_file(self):
        content = "This is test content"
        file = SimpleUploadedFile("test_file.txt", content.encode('utf-8'))

        response = self.client.post(reverse('import_file'), {
            'file': file,
            'tags': 'import,test'
        })

        self.assertTrue(Note.objects.filter(title='test_file').exists())
        note = Note.objects.get(title='test_file')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('note_detail', args=[note.pk]))

        self.assertEqual(note.content, content)
        self.assertEqual(note.tags.count(), 2)
        self.assertIn('import', note.tags.names())
        self.assertIn('test', note.tags.names())


    def test_import_binary_file(self):
        binary_data = bytes([0x80, 0x81, 0x82, 0x83])
        file = SimpleUploadedFile("binary_file.bin", binary_data)

        response = self.client.post(reverse('import_file'), {'file': file})

        self.assertTrue(Note.objects.filter(title='binary_file').exists())
        note = Note.objects.get(title='binary_file')

        self.assertIn("The file you tried to upload has an unsupported file type", note.content)


    def test_import_markdown_file(self):
        content = "# Markdown Test\n\n**Bold text**"
        file = SimpleUploadedFile("test.md", content.encode('utf-8'))

        self.client.post(reverse('import_file'), {'file': file})

        note = Note.objects.get(title='test')
        self.assertEqual(note.content, content)
        html_content = note.get_html_content()
        self.assertIn("<h1>Markdown Test</h1>", html_content)
        self.assertIn("<strong>Bold text</strong>", html_content)


class AISummarizationTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = '/notepage/api/summarize/'  
        self.note = Note.objects.create(
            title="TEST",
            content="Caching tests is for the weak."
        )


    @patch('notepage.views.OpenAI') 
    def test_summarize_note_success(self, mock_openai):

        mock_client = mock_openai.return_value
        mock_client.chat.completions.create.return_value = type('obj', (object,), {
            'choices': [type('obj', (object,), {
                'message': type('obj', (object,), {
                    'content': 'This is a test summary.'
                })
            })]
        })()

        response = self.client.post(self.url, json.dumps({
            'content': 'This is a long test note that needs summarizing.',
            'note_id': self.note.pk
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('summary', response.json())
        self.assertEqual(response.json()['summary'], 'This is a test summary.')


    @patch('notepage.views.OpenAI') 
    def test_summarize_note_missing_content(self, mock_openai):
        mock_openai.return_value.chat.completions.create.return_value = type('obj', (object,), {
            'choices': [type('obj', (object,), {
                'message': type('obj', (object,), {
                    'content': 'Empty summary.'
                })
            })]
        })()

        response = self.client.post(self.url, json.dumps({
            'content': '',
            'note_id': self.note.pk
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('summary', response.json())
        self.assertEqual(body['summary'], 'Empty summary.')


class MultiNoteQuizTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('generate_multi_note_quiz')
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        self.note1 = Note.objects.create(title="Note 1", content="Content about Python", user=self.user)
        self.note2 = Note.objects.create(title="Note 2", content="Content about Django", user=self.user)


    @patch('notepage.views.OpenAI')
    def test_generate_quiz_success(self, mock_openai):
        mock_client = mock_openai.return_value
        mock_client.chat.completions.create.return_value = type('obj', (object,), {
            'choices': [type('obj', (object,), {
                'message': type('obj', (object,), {
                    'content': '{"questions":[{"question":"What is Dog?","choices":["A human","An animal","A program","A food"],"answer":"A language"}]}'
                })
            })]
        })()

        response = self.client.post(self.url, json.dumps({
            'note_ids': [self.note1.id, self.note2.id]
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('quiz', response.json())
        self.assertIn('questions', json.loads(response.json()['quiz']))


    @patch('notepage.views.OpenAI')
    def test_generate_quiz_empty_note_ids(self, mock_openai):
        mock_openai.return_value.chat.completions.create.return_value = type('obj', (object,), {
            'choices': [type('obj', (object,), {
                'message': type('obj', (object,), {
                    'content': '{"questions":[]}'
                })
            })]
        })  ()

        response = self.client.post(self.url, json.dumps({
            'note_ids': []
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertIn('quiz', response.json())


    def test_generate_quiz_invalid_request(self):
        response = self.client.post(self.url, json.dumps({
            'invalid_field': [123]
        }), content_type='application/json')

        self.assertEqual(response.status_code, 500)
        self.assertIn('quiz', response.json())


    @patch('notepage.views.OpenAI')
    def test_generate_quiz_openai_failure(self, mock_openai):
        mock_openai.side_effect = Exception("Mock OpenAI error")

        response = self.client.post(self.url, json.dumps({
            'note_ids': [self.note1.id]
        }), content_type='application/json')

        self.assertEqual(response.status_code, 500)
        self.assertIn('quiz', response.json())
        self.assertTrue(response.json()['quiz'].startswith("Error"))

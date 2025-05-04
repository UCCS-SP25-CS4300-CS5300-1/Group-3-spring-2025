from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from .models import Note
from .forms import NoteForm
from .forms import FileImportForm
from taggit.models import Tag
import json
from openai import OpenAI
import os
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import docx


@csrf_exempt
@login_required
def note_list(request):

    user_notes = Note.objects.filter(user=request.user)
    tags = Tag.objects.filter(note__in=user_notes).distinct()
    search_query = request.GET.get('search', '')
    tag_query = request.GET.get('tag', '')

    if search_query:
        notes = Note.objects.filter(user=request.user).filter(
            Q(title__icontains=search_query) | Q(content__icontains=search_query)
        ).order_by('-updated_at')
    elif tag_query:
        notes = Note.objects.filter(user=request.user).filter(tags__name__in=[tag_query]).order_by('-updated_at')
    else:
        notes = Note.objects.filter(user=request.user).order_by('-updated_at')

    return render(request, 'notepage/note_list.html', {'notes': notes, 'tags': tags})


@csrf_exempt
@login_required
def create_note(request):

    if request.method == 'POST':
        form = NoteForm(request.POST)
        print("Form submitted!")
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            form.save_m2m()
            print(f"Note saved with ID: {note.pk}")
            return redirect('note_detail', pk=note.pk)
        else:
            print("Form errors:", form.errors)
    else:
        form = NoteForm()

    return render(request, 'notepage/note_form.html', {'form': form, 'action': 'Create'})


@csrf_exempt
@login_required
def note_detail(request, pk):

    note = get_object_or_404(Note, pk=pk, user=request.user)
    return render(request, 'notepage/note_detail.html', {'note': note})


@csrf_exempt
@login_required
def edit_note(request, pk):

    note = get_object_or_404(Note, pk=pk, user=request.user)

    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)

        if form.is_valid():
            note = form.save(commit=False)
            note.save()
            return redirect('note_detail', pk=note.pk)

    else:
        form = NoteForm(instance=note)


    return render(request, 'notepage/note_form.html', {'form': form, 'note': note, 'action': 'Edit'})


@csrf_exempt
@login_required
def delete_note(request, pk):

    note = get_object_or_404(Note, pk=pk, user=request.user)

    if request.method == 'POST':
        note.delete()
        return redirect('note_list')

    return render(request, 'notepage/note_confirm_delete.html', {'note': note})


@csrf_exempt
@login_required
def autosave_note(request):

    if request.method == 'POST':
        data = json.loads(request.body)
        note_id = data.get('note_id')
        title = data.get('title')
        content = data.get('content')

        if note_id:
            note = get_object_or_404(Note, pk=note_id)
            note.title = title
            note.content = content
            note.user = request.user
            note.save()
            return JsonResponse({
                'success': True,
                'saved_at': note.updated_at.strftime("%H:%M:%S"),
            })
        else:
            new_note = Note(title=title, content=content, user=request.user)
            new_note.save()
            return JsonResponse({
                'success': True,
                'note_id': new_note.id,
                'saved_at': new_note.updated_at.strftime("%H:%M:%S"),
            })

    return JsonResponse({'success': False})


@csrf_exempt
@login_required
def delete_tags(request):

    if request.method == 'POST':
        notes = Note.objects.filter(user=request.user).all()

        for note in notes:
            note.tags.clear()

        Tag.objects.filter(user=request.user).all().delete()

        return redirect('note_list')


@csrf_exempt
def import_file(request):

    if request.method == 'POST':
        form = FileImportForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            filename = os.path.basename(uploaded_file.name)
            title = os.path.splitext(filename)[0]
            ext = os.path.splitext(filename)[1].lower()

            content = ""
            if ext == '.txt':
                try:
                    content = uploaded_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    content = (
                        f"This note was created from file: {filename}\n\n"
                        "The file content could not be displayed as text."
                    )
            elif ext == '.md':
                try:
                    content = uploaded_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    content = (
                        f"This note was created from file: {filename}\n\n"
                        "The file content could not be displayed as text."
                    )
            elif ext == '.docx':
                try:
                    doc = docx.Document(uploaded_file)
                    content = '\n\n'.join([paragraph.text for paragraph in doc.paragraphs])
                except Exception as e:
                    content = f"This note was created from file: {filename}\n\nError reading the document: {str(e)}"
            else:
                content = (
                    f"The file you tried to upload has an unsupported file type ({ext})."
                    "Please delete this note and upload a file with a support file type."
                )

            note = Note(title=title, content=content, user = request.user)
            note.save()

            tags = form.cleaned_data.get('tags')
            if tags:
                note.tags.add(*tags.split(','))

            return redirect('note_detail', pk=note.pk)
    else:
        form = FileImportForm()

    return render(request, 'notepage/import_file.html', {'form': form})


@csrf_exempt
def get_note_content(request, pk):

    try:
        note = Note.objects.filter(user=request.user).get(pk=pk)
        return JsonResponse({'content': note.content})
    except Note.DoesNotExist:
        return JsonResponse({'error': 'Note not found'}, status=404)


@csrf_exempt
def summarize_note(request):

    if request.method == 'POST':
        try:

            data = json.loads(request.body)
            content = data.get('content', '')
            note_id = data.get('note_id', None)

            note = get_object_or_404(Note, pk=note_id)

            if note.summary and note.content == content:
                return JsonResponse({'summary': note.summary})
            
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))   
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Summarize this note in 1-2 sentences."},
                    {"role": "user", "content": content}
                ]
            )
            summary = response.choices[0].message.content

            note.summary = summary
            note.save(update_fields=['summary'])
            
            return JsonResponse({'summary': summary})

        except Exception as e:
            return JsonResponse({'summary': 'Error: ' + str(e)}, status=500)


@csrf_exempt
def multi_note_quiz_page(request):

    notes = Note.objects.filter(user=request.user)
    return render(request, 'notepage/quiz_page.html', {'notes': notes})


@csrf_exempt
def generate_multi_note_quiz(request):

    if request.method == 'POST':
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            data = json.loads(request.body)

            if 'note_ids' not in data or not isinstance(data['note_ids'], list):
                return JsonResponse({'quiz': 'Error: invalid request, note_ids missing or not a list'}, status=500)

            note_ids = data.get('note_ids', [])
            selected_notes = Note.objects.filter(pk__in=note_ids, user=request.user)

            combined_content = "\n\n".join(note.content for note in selected_notes)

            prompt = (
                "Based on the following notes, generate as many multiple-choice quiz questions as you can. "
                "Each question should include 1 correct answer and 3 incorrect answers. "
                "Respond in the following JSON format:\n\n"
                "{\n"
                "  \"questions\": [\n"
                "    {\n"
                "      \"question\": \"...\",\n"
                "      \"choices\": [\"...\", \"...\", \"...\", \"...\"],\n"
                "      \"answer\": \"...\"\n"
                "    },\n"
                "    ...\n"
                "  ]\n"
                "}\n\n"
                f"Notes:\n{combined_content}"
            )

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful quiz generator."},
                    {"role": "user", "content": prompt}
                ]
            )

            quiz = response.choices[0].message.content
            return JsonResponse({'quiz': quiz})

        except Exception as e:
            return JsonResponse({'quiz': f'Error: {str(e)}'}, status=500)

# Generated by Django 5.1.6 on 2025-03-13 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('due_date', models.DateTimeField()),
                ('event_type', models.CharField(choices=[('assignment', 'Assignment'),
                 ('quiz', 'Quiz'), ('test', 'Test')], max_length=10)),
            ],
        ),
    ]

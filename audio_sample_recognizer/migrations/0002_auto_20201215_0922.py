# Generated by Django 3.1.1 on 2020-12-15 08:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('audio_sample_recognizer', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='audiosample',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='audiosamplelabel',
            name='created_by',
        ),
    ]

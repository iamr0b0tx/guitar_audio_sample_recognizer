# Generated by Django 3.1.1 on 2020-12-15 15:08

import audio_sample_recognizer.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audio_sample_recognizer', '0006_auto_20201215_1600'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audiosample',
            name='audio',
            field=models.FileField(upload_to=audio_sample_recognizer.models.audio_sample_label_directory_path),
        ),
    ]
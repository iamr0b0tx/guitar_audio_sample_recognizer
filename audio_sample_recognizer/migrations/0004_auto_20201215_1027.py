# Generated by Django 3.1.1 on 2020-12-15 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audio_sample_recognizer', '0003_auto_20201215_0958'),
    ]

    operations = [
        migrations.AlterField(
            model_name='audiosample',
            name='audio',
            field=models.FileField(upload_to='audio_samples'),
        ),
        migrations.AlterField(
            model_name='audiosamplelabel',
            name='label',
            field=models.CharField(max_length=128, unique=True),
        ),
    ]

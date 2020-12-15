from django.db import models

# const
AUDIO_SAMPLES_DIR = "audio_samples"


def audio_sample_label_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/audio_samples/<filename>
    return f'{AUDIO_SAMPLES_DIR}/{instance.audio_sample_label.label}/{filename}'


class AudioSampleLabel(models.Model):
    label = models.CharField(max_length=128, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.label


class AudioSample(models.Model):
    audio_sample_label = models.ForeignKey(AudioSampleLabel, on_delete=models.CASCADE)
    audio = models.FileField(upload_to=audio_sample_label_directory_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.audio_sample_label.label


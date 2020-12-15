from django.contrib import admin

from .models import AudioSample, AudioSampleLabel, AudioSampleRecognizerModel


# Register your models here.
class AudioSampleLabelAdmin(admin.ModelAdmin):
    list_display = ("label", "updated_at", "created_at")


class AudioSampleAdmin(admin.ModelAdmin):
    list_display = ('audio_sample_label', "updated_at", "created_at")

    def audio_sample_label(self, obj):
        return obj.audio_sample_label.label
    audio_sample_label.short_description = 'AudioSampleLabel'


class AudioSampleRecognizerModelAdmin(admin.ModelAdmin):
    list_display = ('model', "created_at")


admin.site.register(AudioSample, AudioSampleAdmin)
admin.site.register(AudioSampleLabel, AudioSampleLabelAdmin)
admin.site.register(AudioSampleRecognizerModel, AudioSampleRecognizerModelAdmin)

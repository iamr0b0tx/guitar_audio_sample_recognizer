from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

admin.site.site_title = admin.site.index_title = admin.site.site_header = "Guitar Sample Recognizer"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("audio_sample_recognizer.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
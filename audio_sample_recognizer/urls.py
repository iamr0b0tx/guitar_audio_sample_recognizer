from django.urls import path
from audio_sample_recognizer import views

urlpatterns = [
    path('record/<int:user_id>/<str:audio_sample_label>/predict', views.predict),
    path('record/<int:user_id>/<str:audio_sample_label>/', views.record),
    path('', views.index),
]

# faceapp/urls.py
from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('register-face/', FaceRegisterView.as_view(), name='register-face'),
    path('delete-face/', delete_face, name='delete-face'),
    path('mark-attendance/', FaceAttendanceView.as_view(), name='mark-attendance'),
    path('get-face-uploads/<str:employee_id>/', get_face_uploads, name='get-face-uploads'),
    path('get-face-scans/<str:employee_id>/', get_face_scans, name='get-face-scans'),
    path('trigger-training/', trigger_training, name='trigger-training'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

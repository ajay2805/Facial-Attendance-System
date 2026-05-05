from django.urls import path
from .views import RegisterFaceView, MarkAttendanceView

urlpatterns = [
    path('register/', RegisterFaceView.as_view(), name='register'),
    path('mark-attendance/', MarkAttendanceView.as_view(), name='mark-attendance'),
]

from django.db import models
from core.models import Employee

class Face_Recognization(models.Model):
    id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='face')
    timestamp = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)   
    longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=255, null=True, blank=True) 

    def __str__(self):
        return f"{self.employee_id} - {self.timestamp}"

class FaceImageMeta(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    angle = models.CharField(max_length=20)
    capture_time = models.DateTimeField(auto_now_add=True)
    training_status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending')
    ], default='pending')
    image_path = models.CharField(max_length=300)
    face_encoding = models.JSONField(null=True, blank=True) # Store 128-d vector

    def __str__(self):
        return f"{self.employee.employee_id} - {self.angle} - {self.training_status}"

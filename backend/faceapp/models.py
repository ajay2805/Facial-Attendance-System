from django.db import models
import json

class Person(models.Model):
    name = models.CharField(max_length=255)
    face_encoding_json = models.TextField() # Stores the 128d vector as a JSON string
    created_at = models.DateTimeField(auto_now_add=True)

    def set_encoding(self, encoding_list):
        self.face_encoding_json = json.dumps(encoding_list)

    def get_encoding(self):
        return json.loads(self.face_encoding_json)

    def __str__(self):
        return self.name

class AttendanceRecord(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.person.name} at {self.timestamp}"

from django.contrib import admin
from .models import Person, AttendanceRecord

admin.site.register(Person)
admin.site.register(AttendanceRecord)
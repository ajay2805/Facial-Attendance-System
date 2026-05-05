from rest_framework import serializers
from faceapp.models import *

class FaceSerilaizer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()

    class Meta:
        model = Face_Recognization
        fields = '__all__'  # Or explicitly list the fields you need

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"

    def get_employee_id(self, obj):
        return f"{obj.employee.employee_id}"

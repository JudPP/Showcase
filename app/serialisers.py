from rest_framework import serializers
from .models import User, Appointment, Prescriptions
from django.contrib.auth.hashers import make_password

# https://www.django-rest-framework.org/tutorial/1-serialization/
class UserSerialiser(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super(UserSerialiser, self).create(validated_data)

class AppointmentSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['patient', 'practitioner', 'price', 'date', 'time']

class PrescriptionsSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Prescriptions
        fields = ['prescriptioner', 'patient', 'price', 'paymentRequired', 'isRepeating', 'isApproved', 'previousPrescription', 'repeatRequested', 'prescriptionTime']
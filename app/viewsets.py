from .models import User, Appointment, Prescriptions
from .serialisers import UserSerialiser, AppointmentSerialiser, PrescriptionsSerialiser
from rest_framework import viewsets

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerialiser

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerialiser

class PrescriptionsViewSet(viewsets.ModelViewSet):
    queryset = Prescriptions.objects.all()
    serializer_class = PrescriptionsSerialiser
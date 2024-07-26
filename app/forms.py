# app/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from .models import User, Prescriptions, Appointment, Payment
import datetime
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.forms import ModelChoiceField

def get_staff_registration_choices():
    choices = User.Role.choices
    choices.remove(("PATIENT", "Patient"))
    return choices

def get_title_registration_choices():
    choices = User.Title.choices
    return choices

class PaymentForm(forms.ModelForm):
    cardName = forms.CharField(required=False)
    cardNumber = forms.CharField(max_length=16, min_length=16, required=True, validators=[])
    expiry = forms.DateField(widget=forms.SelectDateWidget())
    cvv2 = forms.CharField(max_length=3, min_length=3, required=True)
    class Meta:
        model = Payment
        fields = ('cardName', 'cardNumber', 'expiry', 'cvv2')

class RegistrationForm(UserCreationForm):
    title = forms.ChoiceField(choices=get_title_registration_choices(), required=True)
    birthdate = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = User
        fields = ('username','title', 'first_name', 'last_name', 'birthdate','isNHS', 'email', 'password1', 'password2')

class StaffRegistrationForm(UserCreationForm):
    role = forms.ChoiceField(choices=get_staff_registration_choices(), required=True)
    title = forms.ChoiceField(choices=get_title_registration_choices(), required=True)
    birthdate = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = User
        fields = ('username', 'title', 'first_name', 'last_name', 'birthdate', 'email', 'password1', 'password2', 'role')

    def save(self, commit=True):
        user = super(StaffRegistrationForm, self).save(commit=False)
        user.is_staff = True
        user.is_active = False

        if commit :
            user.save()
            content_type = ContentType.objects.get_for_model(Appointment)
            permission = Permission.objects.filter(content_type=content_type)
            for permission in permission:
                user.user_permissions.add(permission)
            content_type = ContentType.objects.get_for_model(Prescriptions)
            permission = Permission.objects.filter(content_type=content_type)
            for permission in permission:
                user.user_permissions.add(permission)
            content_type = ContentType.objects.get_for_model(User)
            permission = Permission.objects.get(content_type=content_type, codename="view_user")
            user.user_permissions.add(permission)

        return user

class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ("username", "password")

class UpdateForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

class SearchForm(forms.Form):
    user = forms.CharField(max_length=128, label="Name", required=False)
    isNHS = forms.BooleanField(label='Is NHS', required=False)

class PrescriptionsIssueForm(forms.ModelForm):
    #only shows user type patient in form choice
    patient = forms.ModelChoiceField(queryset=User.objects.filter(role__in=[User.Role.PATIENT]))
    class Meta:
        model = Prescriptions
        # fields = ("prescriptioner","patient","price","paymentRequired","isRepeating")
        fields = ("patient","price","paymentRequired","isRepeating")
        exclude = ("prescriptioner", "isApproved")

class UserModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name_and_title()

class AppointmentForm(forms.ModelForm):
    practitioner = UserModelChoiceField(queryset=User.objects.filter(role__in=[User.Role.DOCTOR, User.Role.NURSE]))
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    time = forms.ChoiceField(choices=[])  # Add a ChoiceField for time slots
    duration = forms.ChoiceField(choices=Appointment.DurationChoices.choices)  # Duration selector

    class Meta:
        model = Appointment
        fields = ['practitioner', 'date', 'time', 'duration', 'description']  # Include the 'time' field in the form

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['practitioner'].label = 'Practitioner'
        self.fields['date'].label = 'Date'
        self.fields['time'].label = 'Time'  # Set label for the 'time' field
        self.fields['duration'].label = 'Duration'
        self.fields['time'].choices = self.get_time_choices()  # Populate choices for the 'time' field
        
    def get_time_choices(self):
        start_time = datetime.time(9, 0)  # Start time at 9:00 AM
        end_time = datetime.time(16, 0)   # End time at 4:00 PM
        delta = datetime.timedelta(minutes=30)  
        
        choices = []
        current_time = start_time
        while current_time < end_time:
            choices.append((current_time.strftime('%H:%M'), current_time.strftime('%I:%M %p')))
            current_time = (datetime.datetime.combine(datetime.date(1, 1, 1), current_time) + delta).time()

        return choices

    def save(self, commit=True, *args, **kwargs):
        instance = super().save(commit=False, *args, **kwargs)
        if commit:
            instance.patient = self.user
            instance.save()
        return instance

    def set_user(self, user):
        self.user = user
        
class ForwardAppointmentForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea, label='Forwarding details:')
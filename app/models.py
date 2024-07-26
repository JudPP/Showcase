from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

def get_appointment_price():
    return Price.objects.get_or_create(id=0)

# Perhaps a bit overkill, but it's simple, consistent
# and can be accessed via REST simply.
# TODO: Should this be per role?
class Price(models.Model):
    id = models.AutoField(primary_key=True)
    priceDoctor = models.DecimalField(max_digits=6, decimal_places=2, default=60)
    priceNurse = models.DecimalField(max_digits=6, decimal_places=2, default=30)

class User(AbstractUser):
    class Role(models.TextChoices):
        DOCTOR = "DOCTOR", 'Doctor'
        NURSE = "NURSE", 'Nurse'
        PATIENT = "PATIENT", "Patient"
        ADMIN = "ADMIN", "Admin"

    class Title(models.TextChoices):
        MR = "Mr", "Mr"
        MASTER = "Master", "Master"
        MRS = "Mrs", "Mrs"
        MS = "Ms","Ms"
        MISS = "Miss", "Miss"
        DR = "Dr", "Dr"
        PROF = "Prof", "Prof"
        MX = "Mx", "Mx"
        
    base_role = Role.PATIENT
    
    role = models.CharField(max_length=50, default=Role.PATIENT, choices=Role.choices)
    title = models.CharField(max_length=50, default=Title.MX, choices=Title.choices)
    
    address = models.CharField(max_length=50, default = "Unkown Address")
    birthdate = models.DateField(default="2000-01-01")
    isNHS = models.BooleanField(verbose_name='NHS Patient',default=False)

    REQUIRED_FIELDS = ["role"]

    def clean(self):
        super().clean()

        # Validate the role field
        if self.role not in self.Role.values:
            raise ValidationError({'role': 'Invalid role specified'})
        
    def get_full_name_and_title(self):
        return str(self.role)+", "+str(self.title) +" "+ str(self.first_name) +" "+str(self.last_name)
        
        
    @property
    def cost(self):
        if self.role == self.Role.DOCTOR:
            return Price.objects.get_or_create(id=0)[0].priceDoctor
        elif self.role == self.Role.NURSE:
            return Price.objects.get_or_create(id=0)[0].priceNurse
        else:
            raise ValueError("Could not determine cost!")

class Payment(models.Model):
    cardName = models.CharField(max_length=50)
    cardNumber = models.CharField(max_length=16)
    expiryDate = models.DateField()
    cvv2 = models.CharField(max_length=3)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="patient_payment")

class Appointment(models.Model):
    """ NEEDS TO BE LINKED WITH PATIENT  """
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_appointments')
    """ NEEDS TO BE LINKED WITH PRACTITIONER  """
    practitioner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='practitioner_appointments')
    price = models.DecimalField(max_digits=6, decimal_places=2, default=50)
    date = models.DateField()
    time = models.TimeField(default='09:00') # Default time (e.g., 9:00 AM)
    description = models.CharField(max_length=500, default='')
    isPaid = models.BooleanField(default=False)
    forward_reason = models.CharField(max_length=500, default='')
    
    class DurationChoices(models.IntegerChoices):
        TEN_MINUTES = 10, '10 minutes'
        TWENTY_MINUTES = 20, '20 minutes'
        THIRTY_MINUTES = 30, '30 minutes'
    
    duration = models.IntegerField(choices=DurationChoices.choices, default=DurationChoices.TEN_MINUTES)



    # Getter and setter for 'patient' attribute
    def get_patient(self):
        return self.patient
    def set_patient(self, patient):
        self.patient = patient

    # Getter and setter for 'practitioner' attribute
    def get_practitioner(self):
        return self.practitioner
    def set_practitioner(self, practitioner):
        self.practitioner = practitioner

    # Getter and setter for 'price' attribute
    def get_price(self):
        return self.price
    def set_price(self, price):
        self.price = price

    # Getter and setter for 'date' attribute
    def get_date(self):
        return self.date
    def set_date(self, date):
        self.date = date

    # Getter and setter for 'time' attribute
    def get_time(self):
        return self.time
    def set_time(self, time):
        self.time = time

class Prescriptions(models.Model):
    id = models.AutoField(primary_key=True)
    #doctor/nurse
    prescriptioner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescription_given')
    #patient
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescription_received')
    price = models.DecimalField(max_digits = 6, decimal_places = 2)
    paymentRequired = models.BooleanField(default=False)
    isRepeating = models.BooleanField(default=False)
    isApproved = models.BooleanField(default = False)
    previousPrescription = models.ForeignKey("Prescriptions", on_delete=models.SET_NULL, null = True)
    repeatRequested = models.BooleanField(default = False)
    prescriptionTime = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()

        # Validate the role field
        if self.prescriptioner.role == User.Role.PATIENT:
            raise ValidationError({'prescriptioner': 'patient cannot be prescription'})
        
        # here making it so doctors and nurses cannot be patient.
        if self.patient.role != User.Role.PATIENT :
            raise ValidationError({'patient': 'patient can only be patient'})
        #price
        if self.price < 0:
            raise ValidationError({'price': 'Price cannot be negative'})

    #getter and setters for perscriptioners
    def get_prescriptioner(self):
        return self.prescriptioner

    def set_prescriptioner(self, prescriptioner):
        self.prescriptioner = prescriptioner

    #getter and setters for patient 
    def set_patient(self, patient):
        self.patient = patient

    def get_patient(self):
        return self.patient

    # Getter and setter for 'price' attribute
    def get_price(self):
        return self.price

    def set_price(self, price):
        self.price = price

    # Getter and setter for 'paymentRequired' attribute
    def get_payment_required(self):
        return self.paymentRequired

    def set_payment_required(self, paymentRequired):
        self.paymentRequired = paymentRequired

    # Getter and setter for 'isRepeating' attribute
    def get_is_repeating(self):
        return self.isRepeating

    def set_is_repeating(self, isRepeating):
        self.isRepeating = isRepeating

#class dash_notes(models.Model):
#    notedate = 
#    content = models.TextField()  # Content of the note
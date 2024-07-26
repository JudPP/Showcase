from django.test import TestCase
from django.contrib.auth import get_user_model
from app.models import Appointment, Prescriptions

class UserModelTest(TestCase):
    def setUp(self):
        # Create a test user for each test case
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword',
            role='DOCTOR'  
        )

    def test_user_creation(self):
        """Test that a user is created with the correct role."""
        self.assertEqual(self.user.role, 'DOCTOR')

    def test_default_base_role(self):
        """Test that the default base_role is set correctly."""
        self.assertEqual(self.user.base_role, 'DOCTOR')

    def test_valid_user_role(self):
        """Test that a user can have a valid role, e.g., NURSE."""
        nurse_user = get_user_model().objects.create_user(
            username='nurseuser',
            password='nursepassword',
            email ='nurse@email.com',
            role='NURSE'
        )

        self.assertEqual(nurse_user.role, 'NURSE')

#Test Cases for Appointment
class AppointmentTestCase(TestCase):
    def setUp(self):
        self.appointment = Appointment.objects.create(
            patient='Patient',
            practitioner='Practitioner',
            price=50.00,
            date='2024-03-05',
            length='00:30'
        )

    def test_appointment_price_pass(self):
        """Test for correct price """
        self.assertGreater(self.appointment.get_price(), 0)

    def test_appintment_price_zero_pass(self):
        """Test for Price to be Zero 0 Free """
        zero_price_appointment = Appointment(
            patient='Patient',
            practitioner='Practitioner',
            price= 0,
            date='2024-03-05',
            length='00:30'
        )
        # checks if price is greater than 0 
        self.assertEqual(zero_price_appointment.get_price(), 0)



#Fail
    def test_appintment_price_negative_fail(self):
        """Test appointment price cannot be negative"""
        negative_price_appointment = Appointment(
            patient='Patient',
            practitioner='Practitioner',
            price= -10.00,
            date='2024-03-05',
            length='00:30'
        )
        # checks if price is greater than 0 
        self.assertGreaterEqual(negative_price_appointment.get_price(), 0,
                           "Price should not be negative.")
        
class PrescriptionsTest(TestCase):
    def setUp(self):
        self.prescription = Prescriptions(prescriptioner="Ana", price=20.00, paymentRequired=False, isRepeating=True)
    
    def test_is_prescription_existing(self):
        """Test that the prescription object exists. Fails if the object does not exist.
        """
        self.assertIsNotNone(self.prescription)

    def test_is_price_positive(self):
        """Test that the prescriotion price variable is above or equal to 0.
        """
        self.assertGreaterEqual(self.prescription.get_price(), 0)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login , authenticate, logout
from django.contrib import messages 
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Sum
from .models import User, Appointment, Prescriptions, Price
from .forms import *
from .calendarAPI import get_calendar_events_for, upload_calendar_event, clear_calendar_events, delete_calendar_event
import datetime
import pytz
from django.db import transaction
from datetime import timedelta
import calendar
import io
from django.http import FileResponse
from reportlab.pdfgen import canvas

def is_medical_staff(user):
    return user.role == User.Role.DOCTOR or user.role == User.Role.NURSE

def is_doctor(user):
    return user.role == User.Role.DOCTOR

def is_nurse(user):
    return user.role == User.Role.NURSE

def is_patient(user):
    return user.role == User.Role.PATIENT

def is_admin(user):
    return user.is_superuser

def home(request):
    return render(request, 'app/home.html')

def calculate_turnover(start_date: datetime, end_date: datetime) -> dict[str, float]:
    """Calculates the total turnover between the specified dates."""
    prescriptionsPrice = Prescriptions.objects.filter(prescriptionTime__gte=start_date.strftime("%Y-%m-%d"), prescriptionTime__lte=end_date.strftime("%Y-%m-%d")).aggregate(Sum('price'))
    appointmentsPrice = Appointment.objects.filter(date__gte=start_date.strftime("%Y-%m-%d"), date__lte=end_date.strftime("%Y-%m-%d")).aggregate(Sum('price'))

    turnover = {
        "Prescriptions": int(prescriptionsPrice['price__sum'] or 0),
        "Appointments": int(appointmentsPrice['price__sum'] or 0),
        "Total": int(prescriptionsPrice['price__sum'] or 0) + int(appointmentsPrice['price__sum'] or 0)
    }

    return turnover

def calculate_turnover_daily(date: datetime.date):
    """ Calculates turnover for each day of the specified month."""
    monthStart = date.replace(day=1)
    
    numberOfDaysInMonth = calendar.monthrange(monthStart.year, monthStart.month)[1]
    turnover = [0] * numberOfDaysInMonth

    for i in range(0, numberOfDaysInMonth): 
        delta = timedelta(days=i)
        current = monthStart + delta
        turnover[i] = calculate_turnover(current, current)
    
    return turnover


def calculate_turnover_weekly(date: datetime.date):
    """ Calculates turnover for each week of the specified month."""
    monthStart = date.replace(day=1)
    # Week start might not neccesarily be in the current month.
    weekStart = monthStart - timedelta(days=monthStart.weekday())

    # Populate all weeks with 0 for consistency.
    numberOfWeeksInMonth = len(calendar.monthcalendar(monthStart.year, monthStart.month))
    turnover_data = [0] * numberOfWeeksInMonth

    for i in range(0, numberOfWeeksInMonth): 
        delta = timedelta(weeks=i) # Skip i weeks in.
        current = weekStart + delta

        # Want to get within a week period.
        turnover_data[i] = calculate_turnover(current, current + timedelta(weeks=1))

    return turnover_data


def calculate_turnover_monthly(date: datetime.date):
    """ Calculates turnover for each month of the specified year."""
    yearStart = date.replace(day=1, month=1)

    # Populate all months with 0 for consistency.
    numberOfMonthsInYear = 12
    turnover_data = [0] * numberOfMonthsInYear

    startOfCurrentMonth = yearStart
    for i in range(0, numberOfMonthsInYear):
        # 32 days will ensure we're always in the next month.
        someTimeInNextMonth = startOfCurrentMonth + timedelta(days=32)
        # Ensure's we're actually at the start of the month.
        startOfNextMonth = someTimeInNextMonth.replace(day=1)

        # Want to get from start of current month, to end of current month.
        turnover_data[i] = calculate_turnover(startOfCurrentMonth, startOfNextMonth - timedelta(days=1))
        startOfCurrentMonth = startOfNextMonth

    return turnover_data

@login_required
@user_passes_test(is_admin)
def turnover(request):
    date = datetime.date.today()
    if request.method == "POST":
        if request.POST.get("wanted_date"):
            date = datetime.datetime.strptime(request.POST.get("wanted_date"), "%Y-%m-%d")

    turnoverDaily = calculate_turnover_daily(datetime.date.today())
    turnoverWeekly = calculate_turnover_weekly(datetime.date.today())
    turnoverMonthly = calculate_turnover_monthly(datetime.date.today())

    turnoverAll = {
        "Daily": turnoverDaily,
        "Weekly": turnoverWeekly,
        "Monthly": turnoverMonthly
    }

    return render(request, 'app/turnover.html', {'turnover': turnoverAll, 'date': date.strftime('%Y-%m-%d')})

@login_required
@user_passes_test(is_admin)
def turnover_download(request, date):
    date = datetime.datetime.strptime(date, "%Y-%m-%d")

    def average_turnover(turnover):
        average = 0
        for i in range(len(turnover)):
            average += turnover[i]["Total"]
        return average / len(turnover)


    turnover = calculate_turnover_daily(date)
    average_daily = average_turnover(turnover)

    turnover = calculate_turnover_weekly(date)
    average_weekly = average_turnover(turnover)

    turnover = calculate_turnover_monthly(date)
    average_monthly = average_turnover(turnover)

    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()
    # Create the PDF object, using  the buffer as its "file."
    p = canvas.Canvas(buffer, pagesize='A4')

    # Set font and font size
    p.setFont("Helvetica", 12)

    # Draw company information
    p.drawImage("./app/static/imgs/DOCTOR-icon.jpg", 450, 680, 100, 100)
    p.drawString(50, 750, "SmartCare Surgery: Turnover " + date.strftime("%Y-%m-%d"))
    p.drawString(50, 730, "123 Lorem Ipsum, Ana Has Apples, UK")
    p.drawString(50, 710, "Phone: 07840123456")
    p.drawString(50, 690, "Email: info@smartcaresurgery.com")

    # Draw horizontal line
    p.line(50, 680, 550, 680)

    # Draw invoice information
    p.drawString(50, 650, "Average Daily Turnover: " + str(average_daily))

    # Draw horizontal line
    p.line(50, 570, 550, 570)

    # Draw appointment information
    p.drawString(50, 550, "Average Weekly Turnover: " + str(average_weekly))

    # Draw horizontal line
    p.line(50, 450, 550, 450)

    p.drawString(50, 430, "Average Monthly Turnover: " + str(average_monthly))

    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename="turnover.pdf")

def login_user(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.data.get('username')
            password = form.data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                print('Redirecting to home')
                return redirect('home')
            else:
                messages.success(request,('There was an error logging in, please try again'))
                # return render(request, 'login/' {'messages':messages})
                return redirect('login')
        else:
            messages.success(request,(form.get_invalid_login_error()))
            # return render(request, 'login/' {'messages':messages})
            return redirect('login')
    else:
        form = LoginForm()
        return render(request, 'registration/login.html', {"form":form})

@login_required
def logout_user(request):
    logout(request)
    messages.success(request,('Logout Successful'))
    return redirect('home')

@transaction.atomic
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            address = request.POST.get('address')  # Get the address from the form data
            user = form.save(commit=False)
            user.address = address
            user.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


def staff_register(request):
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = StaffRegistrationForm()

    return render(request, 'registration/staff_register.html', {'form': form})

@login_required
def dashboard(request):
    if request.user.is_superuser:
        role = "ADMIN"
    else:
        role = request.user.role  
    username = request.user.username
    email = request.user.email
    title = request.user.title
    first_name = request.user.first_name
    last_name = request.user.last_name
    last_login = request.user.last_login
    date_joined = request.user.date_joined
    address = request.user.address

    # Pass the username and role to the template context
    context = {
        'username': username,
        'role': role,
        'email': email,
        'title': title,
        'first_name': first_name,
        'last_name': last_name,
        'last_login': last_login,
        'date_joined': date_joined,
        'address': address
        }
    
    role_str = request.user.role.lower()
    template_name = f'app/dashboard.html'
    
    # Perform role-specific logic here if needed
    
    return render(request, template_name, context)

def clear_google_schedule(request):
    
    clear_calendar_events()

    
    return render(request, 'app/home.html')

@login_required
@user_passes_test(is_medical_staff)
def schedule(request):
    
    events = get_calendar_events_for(request.user)
    
    context = {'events':events}
    
    return render(request, 'app/schedule.html', context)

@login_required
def prescriptions(request):
    role = request.user.role  
    #pulls list of prescriptions based on current user.
    username = request.user
    # Pass the username and role to the template context
    if role == User.Role.PATIENT:
        #prescriptions given to the user
        prescriptions = username.prescription_received.all()
        context = {'prescriptions': prescriptions}
        return render(request, 'app/prescriptions_patient.html', context)
    else:
        #prescriptions made by the user
        prescriptions = username.prescription_given.all()
        context = {'prescriptions': prescriptions}
        return render(request, 'app/prescriptions.html', context)

@login_required
@user_passes_test(is_medical_staff)
def prescription_issue(request):
    if request.method == 'POST':
        form = PrescriptionsIssueForm(request.POST)
        #uses the current logged in user
        form.instance.prescriptioner = request.user
        form.instance.isApproved = True
        if form.is_valid():
            form.save()
            messages.success(request,('Prescription has been successfully issued'))
            return redirect('prescriptions')  # Redirect to the dashboard after prescription
    else:
        form = PrescriptionsIssueForm()
    
    return render(request, 'app/prescriptionissue.html', {'form': form})

@login_required
def appointment(request):
    role = request.user.role 

    if role == User.Role.PATIENT:
        if request.method == 'POST':
            form = AppointmentForm(request.POST)
            form.set_user(request.user)
            if form.is_valid():
                appointment = form.save(commit=False)
                appointment.patient = request.user

                #price based on doc or nurse
                appointment.price = (float(appointment.practitioner.cost)*(appointment.duration/10))

                # Check if the practitioner is already booked at the same date and time
                existing_appointment = Appointment.objects.filter(practitioner=appointment.practitioner, date=appointment.date, time=appointment.time).exists()
                if existing_appointment:
                    messages.error(request, 'This slot is unavailable.')
                    return redirect('appointment')  # Redirect to home page with error message

                appointment.save()

                # Extract date and time from the saved appointment
                appointment_datetime = datetime.datetime.combine(appointment.date, appointment.time)

                # Assuming the timezone of the user is used for the appointment
                appointment_datetime = pytz.timezone('GMT').localize(appointment_datetime)

                duration = datetime.timedelta(minutes=int(appointment.duration))

                # Get patient and practitioner names
                patient_name = appointment.patient.username
                doctor_name = appointment.practitioner.username

                # Upload event to calendar
                upload_calendar_event(appointment_datetime, duration, patient_name, doctor_name, appointment.id)

                return redirect('appointment')
        else:
            form = AppointmentForm()
            form.set_user(request.user)
            appointments = Appointment.objects.filter(patient=request.user)
        
        return render(request, 'app/appointment_book.html', {'form': form, 'appointments': appointments})
    
    else:
        practitioners = User.objects.filter(role__in=[User.Role.DOCTOR, User.Role.NURSE])
        selected_practitioner_id = request.GET.get('practitioner_id')

        if role == User.Role.ADMIN:
            appointments = Appointment.objects.filter(practitioner_id=selected_practitioner_id).order_by('date', 'time') if selected_practitioner_id else Appointment.objects.order_by('date', 'time')
        else:
            appointments = Appointment.objects.filter(practitioner=request.user).order_by('date', 'time')

        price = Price.objects.get_or_create(id=0)[0]
        if request.method == "POST":
            if request.POST.get("doctor_price") or request.POST.get("nurse_price"):
                price.priceDoctor = request.POST.get("doctor_price")
                price.priceNurse = request.POST.get("nurse_price")
                price.save()

        return render(request, 'app/appointment.html', {
            'appointments': appointments,
            'practitioners': practitioners,
            'selected_practitioner_id': int(selected_practitioner_id) if selected_practitioner_id else None,
            'doctor_price': price.priceDoctor,
            'nurse_price': price.priceNurse
        })
        
@login_required  
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.method == 'POST':
        delete_calendar_event(appointment.id)
        appointment.delete()
    return redirect(request.META.get('HTTP_REFERER', 'appointment'))

@login_required
def forward_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.method == 'POST':
        form = ForwardAppointmentForm(request.POST)
        if form.is_valid():
            appointment.forward_reason = form.cleaned_data['reason']
            appointment.save()
            messages.success(request, "Appointment has been forwarded with your provided reason.")
            return redirect('appointment')
        else:
            messages.error(request, "Please provide a valid reason.")
    else:
        form = ForwardAppointmentForm()

    context = {
        'form': form,
        'appointment_id': appointment_id
    }
    return render(request, 'app/forward_appointment.html', context)


@login_required
@user_passes_test(is_patient)
def prescription_repeat(request):
    if request.method == "POST":
        if request.POST.get("prescriptionid"):
            id = request.POST.get("prescriptionid")
            prescription = get_object_or_404(Prescriptions, pk=id)
            prescription2 = Prescriptions(prescriptioner = prescription.prescriptioner, patient = prescription.patient, price = prescription.price, paymentRequired = prescription.paymentRequired, isRepeating = prescription.isRepeating, previousPrescription = prescription)
            if prescription2.patient.isNHS == False:
                prescription2.paymentRequired = True
            prescription2.save()
            prescription.repeatRequested = True
            prescription.save()
    return redirect('prescriptions')

#Approval can only be done by issuer
@login_required
@user_passes_test(is_medical_staff)
def prescription_approval(request):
    if request.method == "POST":
        if request.POST.get("prescriptionid") and request.POST.get("approval"):
            id = request.POST.get("prescriptionid")
            approval = request.POST.get("approval")
            prescription = get_object_or_404(Prescriptions, pk=id)
            if approval == "1":
                prescription.isApproved = True
                prescription.save()
            elif approval == "0":
                if prescription.previousPrescription:
                    prescription.previousPrescription.repeatRequested = False
                    prescription.previousPrescription.save()
                prescription.delete()
    return redirect('prescriptions')


#doc and nurse search up patient.
@login_required
@user_passes_test(is_medical_staff)
def patient_search(request):
    if request.method == "POST":
        if request.POST.get("patient_search"):
            username = request.POST.get("patient_search")
            #only patients are searchable
            patient_usernames = User.objects.filter(username__icontains = username, role = User.Role.PATIENT).all()
            context = {'usernames':patient_usernames}
            return render(request, 'app/patient_search.html', context)
    return render(request, 'app/patient_search.html')


@login_required
@user_passes_test(is_medical_staff)
def patient_data(request, patient_username):
    patient_user = get_object_or_404(User, username=patient_username)
    prescriptions = Prescriptions.objects.filter(patient=patient_user).all()
    if not prescriptions:
        messages.error(request,('There are no prescriptions for this user'))
    return render(request, 'app/patient_search.html', {'prescriptions': prescriptions, 'searched_user':patient_user})

@login_required
@user_passes_test(is_admin)
def user_list(request):
    user_list = User.objects.all().order_by('id')

    if request.method == "POST":
        form = SearchForm(request.POST)
        user_name = request.POST.get("user")
        isNHS = request.POST.get("isNHS")
        user_list = user_list.filter(username__icontains=user_name).filter(isNHS=isNHS=='on')
    else:
        form = SearchForm()

    paginator = Paginator(user_list, 25)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "app/user_list.html", {"form": form, "page_obj": page_obj})

@login_required
@user_passes_test(is_admin)
def user_update(request, id):
    user = User.objects.get(pk=id)
    if request.method == "POST":
        form = UpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return render(request, 'app/user_update.html', {'form': form})
    else:
        form = UpdateForm(instance=user)
    return render(request, 'app/user_update.html', {'form': form, 'user': user})

@login_required
@user_passes_test(is_admin)
def user_delete(request, id):
    user = User.objects.get(pk=id)
    if user:
        user.delete()
        return redirect("/user")
    return redirect("/user")

@login_required
@user_passes_test(is_admin)
def user_approve(request, id):
    user = User.objects.get(pk=id)
    if user:
        user.is_active = True
        user.save()
        return redirect("/user")
    return redirect("/user")

@login_required
@user_passes_test(is_medical_staff)
def invoice(request):
    base_rate = 20
    role = request.user.role 
    if role == User.Role.DOCTOR:
        price = base_rate * 2
    else:
        #nurse
        price = base_rate

#TODO 
"""
Pass through values found from appointments. 

Price diff for nurse and doctor
"""
@login_required
def invoice_download(request):
    if request.method == "POST":
        if request.POST.get("appointmentid"):
            id = request.POST.get("appointmentid")
            appointment = get_object_or_404(Appointment, pk=id)
            # Create a file-like buffer to receive PDF data.
            buffer = io.BytesIO()
            # Create the PDF object, using the buffer as its "file."
            p = canvas.Canvas(buffer, pagesize='A4')

            # Set font and font size
            p.setFont("Helvetica", 12)

            # Draw company information
            p.drawImage("./app/static/imgs/DOCTOR-icon.jpg", 450, 680, 100, 100)
            p.drawString(50, 750, "SmartCare Surgery")
            p.drawString(50, 730, "123 Lorem Ipsum, Ana Has Apples, UK")
            p.drawString(50, 710, "Phone: 07840123456")
            p.drawString(50, 690, "Email: info@smartcaresurgery.com")

            # Draw horizontal line
            p.line(50, 680, 550, 680)

            # Draw invoice information
            p.drawString(50, 650, "Appointment No:")
            p.drawString(150, 650, str(appointment.id))
            p.drawString(50, 630, "Date:")
            p.drawString(150, 630, str(appointment.date))
            p.drawString(50, 610, "Bill To:")
            p.drawString(150, 610, str(appointment.patient.get_full_name()))
            p.drawString(50, 590, "Address:")
            p.drawString(150, 590, str(appointment.patient.address))

            # Draw horizontal line
            p.line(50, 570, 550, 570)

            # Draw appointment information
            p.drawString(50, 550, "Appointment Details: " + str(appointment.description))
            p.drawString(50, 530, "Practitioner: " + str(appointment.practitioner.get_full_name()))
            p.drawString(50, 510, "Date: " + str(appointment.date))
            p.drawString(50, 490, "Time: " + str(appointment.time))
            p.drawString(50, 470, "Price: £" + str(appointment.price))
            

            # Draw horizontal line
            p.line(50, 450, 550, 450)

            # Draw total
            p.drawString(450, 430, "Total: £" + str(appointment.price))

            # Close the PDF object cleanly, and we're done.
            p.showPage()
            p.save()
            # FileResponse sets the Content-Disposition header so that browsers
            # present the option to save the file.
            buffer.seek(0)
            return FileResponse(buffer, as_attachment=False, filename="invoice.pdf")
    return redirect("home")

@login_required
def payment(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if appointment.isPaid == True:
        return redirect('appointment')
    form = PaymentForm()
    if request.method == "POST":
        form = PaymentForm(request.POST)
        form.user = appointment.patient
        if form.is_valid():
            appointment.isPaid = True
            appointment.save()
            return redirect('appointment')
    return render(request, "app/payment.html", {"appointment": appointment, "form": form})

@login_required
def payment_pres(request, prescription_id):
    prescription = get_object_or_404(Prescriptions, pk=prescription_id)
    if prescription.paymentRequired == False:
        return redirect('prescriptions')
    form = PaymentForm()
    if request.method == "POST":
        form = PaymentForm(request.POST)
        form.user = prescription.patient
        if form.is_valid():
            prescription.paymentRequired = False
            prescription.save()
            return redirect('prescriptions')
    return render(request, "app/payment.html", {"prescription": prescription, "form": form})

@user_passes_test(is_admin)
def wipe_users(request):
    users = User.objects.all()
    for user in users:
        if user.username != "admin":
            user.delete()
    return render(request, 'app/home.html')


@login_required
def invoice_prescription_download(request):
    if request.method == "POST":
        if request.POST.get("prescriptionid"):
            id = request.POST.get("prescriptionid")
            prescription = get_object_or_404(Prescriptions, pk=id)
            # Create a file-like buffer to receive PDF data.
            buffer = io.BytesIO()
            # Create the PDF object, using the buffer as its "file."
            p = canvas.Canvas(buffer, pagesize='A4')

            # Set font and font size
            p.setFont("Helvetica", 12)

            # Draw company information
            p.drawImage("./app/static/imgs/DOCTOR-icon.jpg", 450, 680, 100, 100)
            p.drawString(50, 750, "SmartCare Surgery")
            p.drawString(50, 730, "123 Lorem Ipsum, Ana Has Apples, UK")
            p.drawString(50, 710, "Phone: 07840123456")
            p.drawString(50, 690, "Email: info@smartcaresurgery.com")

            # Draw horizontal line
            p.line(50, 680, 550, 680)

            # Draw invoice information
            p.drawString(50, 650, "Prescription No:")
            p.drawString(150, 650, str(prescription.id))
            p.drawString(50, 630, "Date:")
            p.drawString(150, 630, str(prescription.prescriptionTime))
            p.drawString(50, 610, "Bill To:")
            p.drawString(150, 610, str(prescription.patient.get_full_name()))
            p.drawString(50, 590, "Address:")
            p.drawString(150, 590, str(prescription.patient.address))

            # Draw horizontal line
            p.line(50, 570, 550, 570)

            # Draw prescription information
            p.drawString(50, 550, "Practitioner: " + str(prescription.prescriptioner.get_full_name()))
            p.drawString(50, 530, "Price: £" + str(prescription.price))

            

            # Draw horizontal line
            p.line(50, 450, 550, 450)

            # Draw total
            p.drawString(450, 430, "Total: £" + str(prescription.price))

            # Close the PDF object cleanly, and we're done.
            p.showPage()
            p.save()
            # FileResponse sets the Content-Disposition header so that browsers
            # present the option to save the file.
            buffer.seek(0)
            return FileResponse(buffer, as_attachment=False, filename="invoice.pdf")
    return redirect("home")
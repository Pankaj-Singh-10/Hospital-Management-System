import os
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import User, DoctorProfile, PatientProfile
from bookings.models import AvailabilitySlot, Booking
import requests
from django.conf import settings
import json
from datetime import datetime, timedelta
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Google Calendar Helper
class GoogleCalendarHelper:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    @staticmethod
    def get_flow():
        return Flow.from_client_secrets_file(
            'google_client_secrets.json',
            scopes=GoogleCalendarHelper.SCOPES,
            redirect_uri='http://127.0.0.1:8000/google/callback/'
        )
    
    @staticmethod
    def create_event(user, summary, start_time, end_time, attendees):
        if not user.google_calendar_token:
            return None
        
        try:
            credentials = Credentials.from_authorized_user_info(
                user.google_calendar_token,
                GoogleCalendarHelper.SCOPES
            )
            
            service = build('calendar', 'v3', credentials=credentials)
            
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [{'email': email} for email in attendees if email],
                'reminders': {
                    'useDefault': True,
                },
            }
            
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'
            ).execute()
            
            return created_event.get('id')
        except Exception as e:
            print(f"Calendar error: {e}")
            return None

def home(request):
    return render(request, 'home.html')

def doctor_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        specialization = request.POST['specialization']
        
        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            user_type='doctor'
        )
        
        # Create doctor profile
        DoctorProfile.objects.create(
            user=user,
            specialization=specialization
        )
        
        # Send welcome email via serverless function
        try:
            requests.post(settings.EMAIL_SERVICE_URL, json={
                'action': 'SIGNUP_WELCOME',
                'email': email,
                'name': f"Dr. {first_name} {last_name}",
                'user_type': 'doctor'
            }, timeout=2)
        except:
            pass  # Email service might not be running yet
            
        messages.success(request, 'Registration successful! Please login.')
        return redirect('login')
    
    return render(request, 'doctor_signup.html')

def patient_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        phone = request.POST.get('phone', '')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            user_type='patient'
        )
        
        # Create patient profile
        PatientProfile.objects.create(
            user=user,
            phone_number=phone
        )
        
        # Send welcome email via serverless function
        try:
            requests.post(settings.EMAIL_SERVICE_URL, json={
                'action': 'SIGNUP_WELCOME',
                'email': email,
                'name': f"{first_name} {last_name}",
                'user_type': 'patient'
            }, timeout=2)
        except:
            pass
            
        messages.success(request, 'Registration successful! Please login.')
        return redirect('login')
    
    return render(request, 'patient_signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            if user.user_type == 'doctor':
                return redirect('doctor_dashboard')
            else:
                return redirect('patient_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

# Google Calendar OAuth
@login_required
def google_connect(request):
    flow = GoogleCalendarHelper.get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    request.session['google_oauth_state'] = state
    return redirect(authorization_url)

@login_required
def google_callback(request):
    state = request.session.get('google_oauth_state')
    flow = GoogleCalendarHelper.get_flow()
    
    try:
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials
        
        # Store credentials
        request.user.google_calendar_token = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        # Get user's email from calendar
        service = build('calendar', 'v3', credentials=credentials)
        calendar = service.calendars().get(calendarId='primary').execute()
        request.user.google_calendar_email = calendar.get('id')
        request.user.save()
        
        messages.success(request, 'Google Calendar connected successfully!')
    except Exception as e:
        messages.error(request, f'Failed to connect Google Calendar: {e}')
    
    return redirect('dashboard')

# Doctor Views
@login_required
def doctor_dashboard(request):
    if request.user.user_type != 'doctor':
        return redirect('home')
    
    doctor = request.user.doctor_profile
    now = timezone.now()
    
    # Get future slots
    slots = AvailabilitySlot.objects.filter(
        doctor=doctor,
        date__gte=now.date()
    ).order_by('date', 'start_time')
    
    # Get upcoming bookings
    bookings = Booking.objects.filter(
        slot__doctor=doctor,
        slot__date__gte=now.date()
    ).select_related('patient', 'slot').order_by('slot__date', 'slot__start_time')
    
    return render(request, 'doctor_dashboard.html', {
        'slots': slots,
        'bookings': bookings,
        'doctor': doctor,
        'now': now
    })

@login_required
def add_slot(request):
    if request.method == 'POST' and request.user.user_type == 'doctor':
        date = request.POST['date']
        start_time = request.POST['start_time']
        end_time = request.POST['end_time']
        
        # Check if slot exists
        existing = AvailabilitySlot.objects.filter(
            doctor=request.user.doctor_profile,
            date=date,
            start_time=start_time
        ).first()
        
        if existing:
            messages.error(request, 'Slot already exists!')
        else:
            AvailabilitySlot.objects.create(
                doctor=request.user.doctor_profile,
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            messages.success(request, 'Slot added successfully!')
    
    return redirect('doctor_dashboard')

@login_required
def delete_slot(request, slot_id):
    if request.user.user_type == 'doctor':
        try:
            slot = AvailabilitySlot.objects.get(
                id=slot_id,
                doctor=request.user.doctor_profile
            )
            if not slot.is_booked:
                slot.delete()
                messages.success(request, 'Slot deleted!')
            else:
                messages.error(request, 'Cannot delete booked slot!')
        except:
            messages.error(request, 'Slot not found!')
    
    return redirect('doctor_dashboard')

# Patient Views
@login_required
def patient_dashboard(request):
    if request.user.user_type != 'patient':
        return redirect('home')
    
    doctors = DoctorProfile.objects.all().select_related('user')
    return render(request, 'patient_dashboard.html', {
        'doctors': doctors
    })

@login_required
def doctor_slots(request, doctor_id):
    if request.user.user_type != 'patient':
        return redirect('home')
    
    doctor = DoctorProfile.objects.get(id=doctor_id)
    now = timezone.now()
    
    # Only show future, unbooked slots
    slots = AvailabilitySlot.objects.filter(
        doctor=doctor,
        is_booked=False,
        date__gte=now.date()
    ).exclude(
        date=now.date(),
        start_time__lte=now.time()
    ).order_by('date', 'start_time')
    
    return render(request, 'doctor_slots.html', {
        'doctor': doctor,
        'slots': slots
    })

@login_required
def book_slot(request, slot_id):
    if request.user.user_type != 'patient':
        return redirect('home')
    
    # Use transaction and select_for_update to prevent race conditions
    with transaction.atomic():
        try:
            slot = AvailabilitySlot.objects.select_for_update().get(id=slot_id)
            
            if slot.is_booked:
                messages.error(request, 'This slot is already booked!')
                return redirect('patient_dashboard')
            
            if not slot.is_future:
                messages.error(request, 'Cannot book past slots!')
                return redirect('patient_dashboard')
            
            # Create booking
            booking = Booking.objects.create(
                patient=request.user.patient_profile,
                slot=slot
            )
            
            # Mark slot as booked
            slot.is_booked = True
            slot.save()
            
            # Create Google Calendar events
            start_datetime = timezone.make_aware(
                datetime.combine(slot.date, slot.start_time)
            )
            end_datetime = timezone.make_aware(
                datetime.combine(slot.date, slot.end_time)
            )
            
            # Doctor's calendar event
            doctor_event_id = GoogleCalendarHelper.create_event(
                slot.doctor.user,
                f"Appointment with {request.user.get_full_name()}",
                start_datetime,
                end_datetime,
                [request.user.email]
            )
            
            # Patient's calendar event
            patient_event_id = GoogleCalendarHelper.create_event(
                request.user,
                f"Appointment with Dr. {slot.doctor.user.get_full_name()}",
                start_datetime,
                end_datetime,
                [slot.doctor.user.email]
            )
            
            # Send confirmation email via serverless function
            try:
                requests.post(settings.EMAIL_SERVICE_URL, json={
                    'action': 'BOOKING_CONFIRMATION',
                    'email': request.user.email,
                    'patient_name': request.user.get_full_name(),
                    'doctor_name': f"Dr. {slot.doctor.user.get_full_name()}",
                    'date': str(slot.date),
                    'start_time': str(slot.start_time),
                    'end_time': str(slot.end_time)
                }, timeout=2)
            except:
                pass
            
            messages.success(request, 'Booking confirmed! Check your email and Google Calendar.')
            
        except AvailabilitySlot.DoesNotExist:
            messages.error(request, 'Slot not found!')
    
    return redirect('patient_dashboard')

@login_required
def my_bookings(request):
    if request.user.user_type != 'patient':
        return redirect('home')
    
    bookings = Booking.objects.filter(
        patient=request.user.patient_profile
    ).select_related('slot', 'slot__doctor').order_by('-slot__date', '-slot__start_time')
    
    return render(request, 'my_bookings.html', {'bookings': bookings})


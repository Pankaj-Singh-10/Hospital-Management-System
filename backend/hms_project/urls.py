from django.contrib import admin
from django.urls import path
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('doctor-signup/', views.doctor_signup, name='doctor_signup'),
    path('patient-signup/', views.patient_signup, name='patient_signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.patient_dashboard, name='dashboard'),  # Redirect based on role
    path('doctor-dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('add-slot/', views.add_slot, name='add_slot'),
    path('delete-slot/<int:slot_id>/', views.delete_slot, name='delete_slot'),
    path('patient-dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('doctor-slots/<int:doctor_id>/', views.doctor_slots, name='doctor_slots'),
    path('book-slot/<int:slot_id>/', views.book_slot, name='book_slot'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('google/connect/', views.google_connect, name='google_connect'),
    path('google/callback/', views.google_callback, name='google_callback'),
]


from django.db import models
from django.utils import timezone
from accounts.models import User, DoctorProfile, PatientProfile

class AvailabilitySlot(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='availability_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['doctor', 'date', 'start_time']
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.doctor} - {self.date} {self.start_time}-{self.end_time}"
    
    @property
    def is_future(self):
        slot_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date, self.start_time)
        )
        return slot_datetime > timezone.now()
    
    @property
    def is_available(self):
        return not self.is_booked and self.is_future

class Booking(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='bookings')
    slot = models.OneToOneField(AvailabilitySlot, on_delete=models.CASCADE, related_name='booking')
    booked_at = models.DateTimeField(auto_now_add=True)
    google_event_id = models.CharField(max_length=500, blank=True, null=True)
    
    def __str__(self):
        return f"{self.patient} booked with {self.slot.doctor} on {self.slot.date}"
    
    @property
    def doctor(self):
        return self.slot.doctor
    


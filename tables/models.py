from django.db import models
from restaurant.models import Restaurant


class Table(models.Model):
    STATUS_FREE = 'free'
    STATUS_OCCUPIED = 'occupied'
    STATUS_AWAITING_BILL = 'awaiting_bill'
    STATUS_CLEANING = 'cleaning'
    STATUS_RESERVED = 'reserved'

    STATUS_CHOICES = [
        (STATUS_FREE, 'Free'),
        (STATUS_OCCUPIED, 'Occupied'),
        (STATUS_AWAITING_BILL, 'Awaiting Bill'),
        (STATUS_CLEANING, 'Cleaning'),
        (STATUS_RESERVED, 'Reserved'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    number = models.IntegerField()
    capacity = models.IntegerField(default=4)
    zone = models.CharField(max_length=100, blank=True, help_text="e.g., Indoor, Outdoor, Terrace")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_FREE)
    qr_code_url = models.URLField(blank=True, null=True)
    qr_code_local = models.ImageField(upload_to='tables/qrcodes/', blank=True, null=True)
    current_customers = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['number']
        unique_together = ['restaurant', 'number']

    def __str__(self):
        return f"Table {self.number} — {self.restaurant.name} ({self.get_status_display()})"

    def get_status_class(self):
        status_classes = {
            self.STATUS_FREE: 'status-free',
            self.STATUS_OCCUPIED: 'status-occupied',
            self.STATUS_AWAITING_BILL: 'status-awaiting',
            self.STATUS_CLEANING: 'status-cleaning',
            self.STATUS_RESERVED: 'status-reserved',
        }
        return status_classes.get(self.status, 'status-free')

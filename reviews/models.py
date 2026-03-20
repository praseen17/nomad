from django.db import models
from billing.models import Invoice
from workers.models import Worker
import uuid


class Review(models.Model):
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name='review')
    waiter = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    is_used = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.waiter} — {self.rating} stars"

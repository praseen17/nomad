from django.db import models
from django.contrib.auth.models import User
from restaurant.models import Restaurant
import random
import string


def generate_worker_id(prefix):
    digits = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}-{digits}"


class Worker(models.Model):
    ROLE_MANAGER = 'manager'
    ROLE_ASST_MANAGER = 'asst_manager'
    ROLE_RECEPTIONIST = 'receptionist'
    ROLE_WAITER = 'waiter'
    ROLE_CHEF = 'chef'

    ROLE_CHOICES = [
        (ROLE_MANAGER, 'Manager'),
        (ROLE_ASST_MANAGER, 'Assistant Manager'),
        (ROLE_RECEPTIONIST, 'Receptionist'),
        (ROLE_WAITER, 'Waiter'),
        (ROLE_CHEF, 'Chef'),
    ]

    ROLE_PREFIXES = {
        ROLE_MANAGER: 'MGR',
        ROLE_ASST_MANAGER: 'AMG',
        ROLE_RECEPTIONIST: 'RCP',
        ROLE_WAITER: 'WTR',
        ROLE_CHEF: 'CHF',
    }

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='workers')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='worker_profile', null=True, blank=True)
    full_name = models.CharField(max_length=255)
    worker_id = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    avatar_url = models.URLField(blank=True, null=True)
    avatar_local = models.ImageField(upload_to='workers/avatars/', blank=True, null=True)

    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Performance
    tables_handled_today = models.IntegerField(default=0)
    total_orders = models.IntegerField(default=0)

    class Meta:
        ordering = ['role', 'full_name']

    def __str__(self):
        return f"{self.worker_id} — {self.full_name} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        if not self.worker_id:
            prefix = self.ROLE_PREFIXES.get(self.role, 'WRK')
            worker_id = generate_worker_id(prefix)
            while Worker.objects.filter(worker_id=worker_id).exists():
                worker_id = generate_worker_id(prefix)
            self.worker_id = worker_id
        super().save(*args, **kwargs)

    def get_avatar(self):
        if self.avatar_local:
            return self.avatar_local.url
        if self.avatar_url:
            return self.avatar_url
        return None

    def get_dashboard_url(self):
        role_urls = {
            self.ROLE_MANAGER: '/dashboard/manager/',
            self.ROLE_ASST_MANAGER: '/dashboard/asst-manager/',
            self.ROLE_RECEPTIONIST: '/dashboard/reception/',
            self.ROLE_WAITER: '/dashboard/waiter/',
            self.ROLE_CHEF: '/dashboard/chef/',
        }
        return role_urls.get(self.role, '/dashboard/')


class Shift(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='shifts')
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    workers = models.ManyToManyField(Worker, blank=True, related_name='shifts')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"

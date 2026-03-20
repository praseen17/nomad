from django.db import models
from django.contrib.auth.models import User
import uuid


class Restaurant(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Approval'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    TYPE_CHOICES = [
        ('fine_dining', 'Fine Dining'),
        ('casual', 'Casual Dining'),
        ('fast_food', 'Fast Food'),
        ('cafe', 'Café'),
        ('cloud_kitchen', 'Cloud Kitchen'),
        ('other', 'Other'),
    ]

    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='restaurant')
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    restaurant_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    address_street = models.CharField(max_length=255)
    address_city = models.CharField(max_length=100)
    address_state = models.CharField(max_length=100)
    address_pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=20, blank=True)
    gst_number = models.CharField(max_length=50, blank=True)
    fssai_number = models.CharField(max_length=50, blank=True)

    logo_url = models.URLField(blank=True, null=True)
    logo_local = models.ImageField(upload_to='restaurant/logos/', blank=True, null=True)
    banner_url = models.URLField(blank=True, null=True)
    banner_local = models.ImageField(upload_to='restaurant/banners/', blank=True, null=True)
    document_url = models.URLField(blank=True, null=True)

    qr_code_url = models.URLField(blank=True, null=True)
    qr_code_local = models.ImageField(upload_to='restaurant/qrcodes/', blank=True, null=True)
    menu_url = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    rejection_note = models.TextField(blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_logo(self):
        if self.logo_local:
            return self.logo_local.url
        if self.logo_url:
            return self.logo_url
        return None

    def get_banner(self):
        if self.banner_local:
            return self.banner_local.url
        if self.banner_url:
            return self.banner_url
        return None

    def get_menu_link(self):
        return f'/menu/{self.slug}/'


class SuperAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='super_admin_profile')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SuperAdmin: {self.user.email}"


class AuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    actor_name = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.actor_name} - {self.action} at {self.timestamp}"


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

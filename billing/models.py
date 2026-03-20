from django.db import models
from restaurant.models import Restaurant
from tables.models import Table
from orders.models import Order
from workers.models import Worker
import uuid
from datetime import date


def generate_invoice_number():
    today = date.today().strftime('%Y%m%d')
    # Use as_uuid for clarity and to satisfy linter indexing checks
    unique_id = uuid.uuid4().hex.upper()
    unique_fragment = unique_id[0:6]
    return f"INV-{today}-{unique_fragment}"


class Invoice(models.Model):
    PAYMENT_CASH = 'cash'
    PAYMENT_UPI = 'upi'
    PAYMENT_CARD = 'card'
    PAYMENT_SPLIT = 'split'

    PAYMENT_CHOICES = [
        (PAYMENT_CASH, 'Cash'),
        (PAYMENT_UPI, 'UPI'),
        (PAYMENT_CARD, 'Card'),
        (PAYMENT_SPLIT, 'Split Payment'),
    ]

    invoice_number = models.CharField(max_length=30, unique=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='invoices')
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='invoices')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice', null=True)
    waiter = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name='waiter_invoices')
    receptionist = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name='receptionist_invoices')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_type = models.CharField(max_length=10, choices=[('flat', 'Flat (₹)'), ('percent', 'Percentage (%)')], blank=True)
    discount_value = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount_reason = models.TextField(blank=True)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    gst_rate = models.DecimalField(max_digits=4, decimal_places=2, default=5.0)
    gst_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_CASH)
    customer_count = models.IntegerField(default=1)

    review_token = models.UUIDField(default=uuid.uuid4, unique=True)
    review_qr_url = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invoice_number} — ₹{self.grand_total}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = generate_invoice_number()
        super().save(*args, **kwargs)

    def generate_review_qr_code(self, request):
        if not self.review_qr_code:
            review_url = reverse('review_invoice', kwargs={'token': self.review_token})
            # Use dynamic host so it works on mobile devices on same network
            protocol = 'https' if request.is_secure() else 'http'
            full_url = f"{protocol}://{request.get_host()}{review_url}"

            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(full_url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

            # Save QR code to a BytesIO object
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            filename = f'invoice_review_qr_{self.pk}.png'
            self.review_qr_code.save(filename, File(buffer), save=False)
            self.review_qr_url = full_url # Store the URL for convenience
            self.save(update_fields=['review_qr_code', 'review_qr_url'])


    def calculate_totals(self):
        self.subtotal = self.order.get_total()
        if self.discount_type == 'flat':
            self.discount_amount = self.discount_value
        elif self.discount_type == 'percent':
            self.discount_amount = (self.subtotal * self.discount_value) / 100
        taxable = self.subtotal - self.discount_amount
        self.gst_amount = (taxable * self.gst_rate) / 100
        self.grand_total = taxable + self.gst_amount
        self.save()

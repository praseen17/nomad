from django.db import models
from restaurant.models import Restaurant
from tables.models import Table
from menu.models import Dish
from workers.models import Worker


class Order(models.Model):
    STATUS_OPEN = 'open'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='orders')
    waiter = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, blank=True, related_name='waiter_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    customer_count = models.IntegerField(default=1)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} — Table {self.table.number}"

    def get_total(self):
        return sum(item.get_subtotal() for item in self.items.all())

    def get_item_count(self):
        return self.items.count()


class OrderItem(models.Model):
    ITEM_STATUS_PENDING = 'pending'
    ITEM_STATUS_IN_KITCHEN = 'in_kitchen'
    ITEM_STATUS_SERVED = 'served'
    ITEM_STATUS_CANCELLED = 'cancelled'

    ITEM_STATUS_CHOICES = [
        (ITEM_STATUS_PENDING, 'Pending'),
        (ITEM_STATUS_IN_KITCHEN, 'In Kitchen'),
        (ITEM_STATUS_SERVED, 'Served'),
        (ITEM_STATUS_CANCELLED, 'Cancelled'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=ITEM_STATUS_CHOICES, default=ITEM_STATUS_PENDING)
    notes = models.TextField(blank=True)

    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.dish.name} x{self.quantity} — Order #{self.order.id}"

    def get_subtotal(self):
        return self.unit_price * self.quantity

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.dish.price
        super().save(*args, **kwargs)

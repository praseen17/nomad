from django.db import models
from restaurant.models import Restaurant


class MenuCategory(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_categories')
    name = models.CharField(max_length=100)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Menu Categories'

    def __str__(self):
        return f"{self.restaurant.name} — {self.name}"


class Dish(models.Model):
    VEG = 'veg'
    NON_VEG = 'non_veg'
    VEGAN = 'vegan'

    FOOD_TYPE_CHOICES = [
        (VEG, 'Vegetarian'),
        (NON_VEG, 'Non-Vegetarian'),
        (VEGAN, 'Vegan'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='dishes')
    category = models.ForeignKey(MenuCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='dishes')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    food_type = models.CharField(max_length=10, choices=FOOD_TYPE_CHOICES, default=VEG)

    image_url = models.URLField(blank=True, null=True)
    image_local = models.ImageField(upload_to='dishes/', blank=True, null=True)

    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'display_order', 'name']
        verbose_name_plural = 'Dishes'

    @property
    def image(self):
        if self.image_local:
            return self.image_local
        return None

    def __str__(self):
        return f"{self.name} — ₹{self.price}"

    def get_image(self):
        if self.image_local:
            return self.image_local.url
        if self.image_url:
            return self.image_url
        return None

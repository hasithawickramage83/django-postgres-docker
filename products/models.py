from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    name = models.CharField(max_length=255)
    product_model = models.CharField(max_length=100, blank=True)  # <--- must be here
    product_dimension = models.CharField(max_length=50, blank=True)
    description = models .TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)  # <-- new field
    discount_percentage = models.PositiveIntegerField(default=0)
    promotion_text = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="products"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def discounted_price(self):
        if self.discount_percentage > 0:
            return self.price - (self.price * self.discount_percentage / 100)
        return self.price

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"

from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products' 
     )
    quantity = models.PositiveIntegerField(default=0) 
    minimum_stock = models.PositiveIntegerField()
    maximum_stock = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def stock_status(self):
     if self.quantity == 0:
        return 'OUT_OF_STOCK'

     if self.quantity <= self.minimum_stock:
        return 'LOW_STOCK'

     return 'IN_STOCK'


    def __str__(self):
        return self.name

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('STAFF', 'Staff'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='STAFF'
    )

    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Category(models.Model):
     name = models.CharField(max_length=100, unique=True)
     description = models.TextField(blank=True)

     class Meta:
         verbose_name_plural = 'categories'

     def __str__(self):
        return self.name

class Supplier(models.Model):
     name = models.CharField(max_length=200)
     contact_person = models.CharField(max_length=150, blank=True)
     phone = models.CharField(max_length=30, blank=True)
     email = models.EmailField(blank=True)
     address = models.TextField(blank=True)

     def __str__(self):
         return self.name

class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUSTMENT', 'Adjustment'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements'
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES
    )

    quantity = models.PositiveIntegerField()

    reason = models.CharField(
        max_length=255,
        blank=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.product.name} - {self.movement_type} - {self.quantity}"

class Notification(models.Model):
     NOTIFICATION_TYPES = [
        ('LOW_STOCK', 'Low Stock'),
        ('OUT_OF_STOCK', 'Out of Stock'),
       
     ]
     product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='notifications',
     )

     user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
     )

     title = models.CharField(max_length=255)

     message = models.TextField()

     notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
     )

     is_read = models.BooleanField(default=False)

     created_at = models.DateTimeField(auto_now_add=True)

     def __str__(self):
        return f"{self.user.username} - {self.title}"

from django.contrib import admin

from .models import (
    Category,
    Notification,
    Product,
    StockMovement,
    Supplier,
    UserProfile,
)


admin.site.register(
    [
        Category,
        Notification,
        Product,
        StockMovement,
        Supplier,
        UserProfile,
    ]
)

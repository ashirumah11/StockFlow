from django.contrib import admin

# Register your models here.
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'quantity', 'price', 'created_at')
    search_fields = ('name', 'sku')
    list_filter = ('created_at',)
import csv

from django.contrib import admin
from django.db.models import F
from django.http import HttpResponse
from django.utils.html import format_html

from .models import (
    Category,
    Notification,
    Product,
    StockMovement,
    Supplier,
    UserProfile,
)


class StockStatusFilter(admin.SimpleListFilter):
    title = 'stock status'
    parameter_name = 'stock_status'

    def lookups(self, request, model_admin):
        return (
            ('in_stock', 'In stock'),
            ('low_stock', 'Low stock'),
            ('out_of_stock', 'Out of stock'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'in_stock':
            return queryset.filter(quantity__gt=F('minimum_stock'))
        if self.value() == 'low_stock':
            return queryset.filter(
                quantity__gt=0,
                quantity__lte=F('minimum_stock'),
            )
        if self.value() == 'out_of_stock':
            return queryset.filter(quantity=0)
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'sku', 'name', 'category', 'quantity', 'stock_status_badge',
        'price', 'updated_at',
    )
    list_display_links = ('sku', 'name')
    list_filter = (StockStatusFilter, 'category', 'supplier', 'created_at')
    search_fields = ('name', 'sku', 'category__name', 'supplier__name')
    ordering = ('name',)
    list_per_page = 25
    autocomplete_fields = ('category', 'supplier')
    readonly_fields = ('quantity', 'stock_status_badge', 'created_at', 'updated_at')
    fieldsets = (
        ('Product identity', {
            'fields': ('name', 'sku', 'image_url', 'category', 'supplier'),
        }),
        ('Stock control', {
            'fields': (
                'quantity', 'minimum_stock', 'maximum_stock', 'stock_status_badge',
            ),
        }),
        ('Pricing and audit', {
            'fields': ('price', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status', ordering='quantity')
    def stock_status_badge(self, obj):
        status = obj.stock_status
        labels = {
            'IN_STOCK': ('In stock', '#155244', '#e3f1eb'),
            'LOW_STOCK': ('Low stock', '#a56a14', '#fff3d9'),
            'OUT_OF_STOCK': ('Out of stock', '#b94f49', '#fbe8e5'),
        }
        label, color, background = labels[status]
        return format_html(
            '<span style="background:{};border-radius:999px;color:{};'
            'display:inline-block;font-size:12px;font-weight:700;padding:4px 9px">'
            '{}</span>', background, color, label,
        )

    @admin.action(description='Export selected products as CSV')
    def export_products(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'
        writer = csv.writer(response)
        writer.writerow(('SKU', 'Name', 'Category', 'Quantity', 'Status', 'Price'))
        for product in queryset.select_related('category'):
            writer.writerow((
                product.sku, product.name,
                product.category.name if product.category else '',
                product.quantity, product.stock_status, product.price,
            ))
        return response

    actions = (export_products,)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        'movement_badge', 'product', 'quantity_display', 'reference',
        'created_by', 'created_at',
    )
    list_filter = ('movement_type', 'created_at')
    search_fields = ('product__name', 'product__sku', 'reference', 'reason')
    ordering = ('-created_at',)
    autocomplete_fields = ('product',)
    historical_fields = (
        'product', 'movement_type', 'quantity', 'reason', 'reference',
        'created_by', 'created_at',
    )
    date_hierarchy = 'created_at'

    def get_readonly_fields(self, request, obj=None):
        return self.historical_fields if obj else ()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return obj is not None

    @admin.display(description='Type')
    def movement_badge(self, obj):
        colors = {
            'IN': ('Stock in', '#155244', '#e3f1eb'),
            'OUT': ('Stock out', '#b94f49', '#fbe8e5'),
            'ADJUSTMENT': ('Adjustment', '#a56a14', '#fff3d9'),
        }
        label, color, background = colors[obj.movement_type]
        return format_html(
            '<span style="background:{};border-radius:999px;color:{};'
            'font-size:12px;font-weight:700;padding:4px 9px">{}</span>',
            background, color, label,
        )

    @admin.display(description='Quantity')
    def quantity_display(self, obj):
        prefix = '+' if obj.movement_type == 'IN' else '-' if obj.movement_type == 'OUT' else '~'
        return format_html('<strong>{}{}</strong>', prefix, obj.quantity)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count', 'description')
    search_fields = ('name', 'description')
    ordering = ('name',)

    @admin.display(description='Products')
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'product_count')
    search_fields = ('name', 'contact_person', 'phone', 'email')
    ordering = ('name',)

    @admin.display(description='Products')
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'product', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'product__name', 'user__username')
    ordering = ('is_read', '-created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('product', 'user')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    autocomplete_fields = ('user',)

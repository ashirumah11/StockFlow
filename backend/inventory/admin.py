from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User

from .models import (
    Category,
    Notification,
    Product,
    StockMovement,
    Supplier,
    UserProfile,
)
from .services import create_stock_movement
from .dashboard import get_dashboard_context


class StockFlowAdminSite(admin.AdminSite):
    site_header = 'StockFlow Administration'
    site_title = 'StockFlow Admin'
    index_title = 'Dashboard'
    index_template = 'admin/stockflow_index.html'

    def index(self, request, extra_context=None):
        context = get_dashboard_context()
        if extra_context:
            context.update(extra_context)
        return super().index(request, extra_context=context)


stockflow_admin_site = StockFlowAdminSite(name='stockflow_admin')
stockflow_admin_site.register(User, UserAdmin)
stockflow_admin_site.register(Group, GroupAdmin)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'sku',
        'category',
        'supplier',
        'quantity',
        'price',
        'created_at',
    )
    search_fields = ('name', 'sku')
    list_filter = ('category', 'supplier', 'created_at')
    readonly_fields = ('quantity',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    search_fields = ('user__username', 'user__email')
    list_filter = ('role',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email')
    search_fields = ('name', 'contact_person', 'phone', 'email')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'movement_type',
        'quantity',
        'reason',
        'created_by',
        'created_at',
    )
    search_fields = (
        'product__name',
        'product__sku',
        'reason',
        'created_by__username',
    )
    list_filter = ('movement_type', 'created_at')
    readonly_fields = (
        'product',
        'movement_type',
        'quantity',
        'reason',
        'created_by',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
            return

        movement = create_stock_movement(
            product=obj.product,
            movement_type=obj.movement_type,
            quantity=obj.quantity,
            reason=obj.reason,
            user=request.user,
        )
        obj.pk = movement.pk
        obj.created_at = movement.created_at
        obj.created_by = movement.created_by


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'title',
        'notification_type',
        'is_read',
        'created_at',
    )
    search_fields = ('user__username', 'title', 'message')
    list_filter = ('notification_type', 'is_read', 'created_at')
    readonly_fields = ('created_at',)


stockflow_admin_site.register(Product, ProductAdmin)
stockflow_admin_site.register(UserProfile, UserProfileAdmin)
stockflow_admin_site.register(Category, CategoryAdmin)
stockflow_admin_site.register(Supplier, SupplierAdmin)
stockflow_admin_site.register(StockMovement, StockMovementAdmin)
stockflow_admin_site.register(Notification, NotificationAdmin)

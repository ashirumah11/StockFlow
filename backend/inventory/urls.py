from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import (
    ProductViewSet,
    CategoryViewSet,
    SupplierViewSet,
    StockMovementViewSet,
    NotificationViewSet,
    DashboardView,
    InventoryReportView,
)



router = DefaultRouter()

router.register(r'products', ProductViewSet, basename='product')
router.register(
    r'categories',
    CategoryViewSet,
    basename='category'
)
router.register(
    r'suppliers',
    SupplierViewSet,
    basename='supplier'
)
router.register(
    r'stock-movements',
    StockMovementViewSet,
    basename='stock-movement'
)
router.register(
    r'notifications',
    NotificationViewSet,
    basename='notification'
)
dashboard_urlpatterns = [
    path(
        'dashboard/',
        DashboardView.as_view(),
        name='dashboard'
    ),
    path(
        'reports/inventory/',
        InventoryReportView.as_view(),
        name='inventory-report'
    ),
]

urlpatterns = dashboard_urlpatterns + router.urls

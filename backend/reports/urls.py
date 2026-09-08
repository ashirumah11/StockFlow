from django.urls import path

from .views import (
    CategoryReportView,
    CurrentStockReportView,
    InventorySummaryReportView,
    MovementReportView,
    SupplierReportView,
    UserActivityReportView,
    current_stock_csv,
)


urlpatterns = [
    path('summary/', InventorySummaryReportView.as_view(), name='report-summary'),
    path('inventory/', InventorySummaryReportView.as_view(), name='report-inventory-legacy'),
    path('current-stock/', CurrentStockReportView.as_view(), name='report-current-stock'),
    path('current-stock/export/', current_stock_csv, name='report-current-stock-csv'),
    path('low-stock/', CurrentStockReportView.as_view(), {'status': 'LOW_STOCK'}, name='report-low-stock'),
    path('out-of-stock/', CurrentStockReportView.as_view(), {'status': 'OUT_OF_STOCK'}, name='report-out-of-stock'),
    path('movements/', MovementReportView.as_view(), name='report-movements'),
    path('stock-in/', MovementReportView.as_view(), {'movement_type': 'IN'}, name='report-stock-in'),
    path('stock-out/', MovementReportView.as_view(), {'movement_type': 'OUT'}, name='report-stock-out'),
    path('adjustments/', MovementReportView.as_view(), {'movement_type': 'ADJUSTMENT'}, name='report-adjustments'),
    path('valuation/', CurrentStockReportView.as_view(), {'report_type': 'valuation'}, name='report-valuation'),
    path('categories/', CategoryReportView.as_view(), name='report-categories'),
    path('suppliers/', SupplierReportView.as_view(), name='report-suppliers'),
    path('user-activity/', UserActivityReportView.as_view(), name='report-user-activity'),
]

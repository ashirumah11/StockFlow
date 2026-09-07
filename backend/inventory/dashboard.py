from django.db import models

from .models import Category, Notification, Product, StockMovement


def get_dashboard_context():
    products = Product.objects.select_related('category', 'supplier')
    total_products = products.count()
    in_stock_count = products.filter(
        quantity__gt=models.F('minimum_stock')
    ).count()
    low_stock_count = products.filter(
        quantity__gt=0,
        quantity__lte=models.F('minimum_stock'),
    ).count()
    out_of_stock_count = products.filter(quantity=0).count()

    def percentage(value):
        return round(value / total_products * 100, 1) if total_products else 0

    return {
        'total_products': total_products,
        'total_stock': sum(product.quantity for product in products),
        'in_stock_count': in_stock_count,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'in_stock_percent': percentage(in_stock_count),
        'low_stock_percent': percentage(low_stock_count),
        'out_of_stock_percent': percentage(out_of_stock_count),
        'low_stock_end_percent': percentage(in_stock_count + low_stock_count),
        'recent_movements': StockMovement.objects.select_related(
            'product', 'created_by'
        ).order_by('-created_at')[:5],
        'low_stock_products': products.filter(
            quantity__lte=models.F('minimum_stock')
        ).order_by('quantity', 'name')[:5],
        'top_products': products.order_by('-quantity', 'name')[:5],
        'recent_notifications': Notification.objects.select_related(
            'product', 'user'
        ).order_by('-created_at')[:5],
    }

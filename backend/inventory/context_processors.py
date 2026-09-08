from django.db.models import F, Sum

from .models import Product, StockMovement


def dashboard_stats(request):
    if not request.path.startswith('/admin/'):
        return {}

    products = Product.objects.all()
    total_products = products.count()
    total_stock = products.aggregate(total=Sum('quantity'))['total'] or 0
    low_stock = products.filter(
        quantity__gt=0,
        quantity__lte=F('minimum_stock'),
    ).count()
    out_of_stock = products.filter(quantity=0).count()
    in_stock = products.filter(quantity__gt=F('minimum_stock')).count()

    return {
        'stockflow_stats': {
            'total_products': total_products,
            'total_stock': total_stock,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'in_stock': in_stock,
            'health_percent': round((in_stock / total_products) * 100)
            if total_products else 0,
            'recent_movements': StockMovement.objects.select_related(
                'product', 'created_by'
            ).order_by('-created_at')[:6],
        },
    }
from datetime import timedelta

from django.db.models import F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import Notification, Product, StockMovement


def dashboard_stats(request):
    if not request.path.startswith('/admin/'):
        return {}

    current_hour = timezone.localtime().hour
    greeting = (
        'evening' if current_hour >= 18
        else 'noon' if current_hour >= 12
        else 'morning'
    )
    products = Product.objects.all()
    total_products = products.count()
    total_stock = products.aggregate(total=Sum('quantity'))['total'] or 0
    low_stock = products.filter(
        quantity__gt=0,
        quantity__lte=F('minimum_stock'),
    ).count()
    out_of_stock = products.filter(quantity=0).count()
    in_stock = products.filter(quantity__gt=F('minimum_stock')).count()
    inventory_value = sum(
        product.quantity * product.price
        for product in products.only('quantity', 'price')
    )
    low_stock_products = products.filter(
        quantity__gt=0,
        quantity__lte=F('minimum_stock'),
    ).select_related('category').order_by('quantity', 'name')[:5]
    category_snapshot = list(
        products.values('category__name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')[:5]
    )

    start_date = timezone.localdate() - timedelta(days=6)
    movement_rows = (
        StockMovement.objects.filter(created_at__date__gte=start_date)
        .annotate(day=TruncDate('created_at'))
        .values('day', 'movement_type')
        .annotate(total=Sum('quantity'))
    )
    movement_totals = {
        (row['day'], row['movement_type']): row['total']
        for row in movement_rows
    }
    movement_chart = [
        {
            'label': (start_date + timedelta(days=offset)).strftime('%a'),
            'stock_in': movement_totals.get(
                (start_date + timedelta(days=offset), 'IN'), 0
            ),
            'stock_out': movement_totals.get(
                (start_date + timedelta(days=offset), 'OUT'), 0
            ),
        }
        for offset in range(7)
    ]
    unread_notifications = []
    unread_notification_count = 0
    if request.user.is_authenticated:
        unread_queryset = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).select_related('product').order_by('-created_at')
        unread_notification_count = unread_queryset.count()
        unread_notifications = list(unread_queryset[:5])

    return {
        'stockflow_stats': {
            'greeting': greeting,
            'total_products': total_products,
            'total_stock': total_stock,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
            'in_stock': in_stock,
            'health_percent': round((in_stock / total_products) * 100)
            if total_products else 0,
            'inventory_value': inventory_value,
            'low_stock_products': low_stock_products,
            'category_snapshot': category_snapshot,
            'movement_chart': movement_chart,
            'unread_notifications': unread_notifications,
            'unread_notification_count': unread_notification_count,
            'recent_movements': StockMovement.objects.select_related(
                'product', 'created_by'
            ).order_by('-created_at')[:6],
        },
    }
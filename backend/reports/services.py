from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import (
    Case,
    Count,
    DecimalField,
    F,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from inventory.models import Category, Product, StockMovement, Supplier


class ReportFilterError(ValueError):
    pass


def parse_date(value, field_name):
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ReportFilterError(
            f'{field_name} must use YYYY-MM-DD format.'
        ) from error


def filtered_products(params):
    queryset = Product.objects.select_related('category', 'supplier')
    category = params.get('category')
    supplier = params.get('supplier')
    status = params.get('status')
    if category:
        queryset = queryset.filter(category_id=category)
    if supplier:
        queryset = queryset.filter(supplier_id=supplier)
    if status == 'IN_STOCK':
        queryset = queryset.filter(quantity__gt=F('minimum_stock'))
    elif status == 'LOW_STOCK':
        queryset = queryset.filter(
            quantity__gt=0,
            quantity__lte=F('minimum_stock'),
        )
    elif status == 'OUT_OF_STOCK':
        queryset = queryset.filter(quantity=0)
    elif status:
        raise ReportFilterError(
            'status must be IN_STOCK, LOW_STOCK, or OUT_OF_STOCK.'
        )
    return queryset.order_by('name')


def product_row(product):
    stock_value = product.quantity * product.price
    return {
        'id': product.id,
        'sku': product.sku,
        'product': product.name,
        'category': product.category.name if product.category else None,
        'supplier': product.supplier.name if product.supplier else None,
        'quantity': product.quantity,
        'minimum_stock': product.minimum_stock,
        'maximum_stock': product.maximum_stock,
        'status': product.stock_status,
        'unit_price': product.price,
        'stock_value': stock_value,
    }


def current_stock_report(params):
    return [product_row(product) for product in filtered_products(params)]


def inventory_summary(params=None):
    rows = current_stock_report(params or {})
    low_stock_products = sum(row['status'] == 'LOW_STOCK' for row in rows)
    out_of_stock_products = sum(
        row['status'] == 'OUT_OF_STOCK' for row in rows
    )
    total_units = sum(row['quantity'] for row in rows)
    return {
        'total_products': len(rows),
        'total_units': total_units,
        'total_stock': total_units,
        'inventory_value': sum(
            (row['stock_value'] for row in rows),
            Decimal('0'),
        ),
        'in_stock_products': sum(row['status'] == 'IN_STOCK' for row in rows),
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'low_stock': low_stock_products,
        'out_of_stock': out_of_stock_products,
    }


def movement_queryset(params):
    queryset = StockMovement.objects.select_related(
        'product', 'product__category', 'product__supplier', 'created_by'
    ).order_by('-created_at')
    start_date = parse_date(params.get('start_date'), 'start_date')
    end_date = parse_date(params.get('end_date'), 'end_date')
    if start_date and end_date and start_date > end_date:
        raise ReportFilterError('start_date cannot be after end_date.')
    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)
    for key, lookup in (
        ('product', 'product_id'),
        ('category', 'product__category_id'),
        ('user', 'created_by_id'),
        ('movement_type', 'movement_type'),
    ):
        value = params.get(key)
        if value:
            queryset = queryset.filter(**{lookup: value})
    movement_type = params.get('movement_type')
    if movement_type and movement_type not in {'IN', 'OUT', 'ADJUSTMENT'}:
        raise ReportFilterError(
            'movement_type must be IN, OUT, or ADJUSTMENT.'
        )
    return queryset


def movement_row(movement):
    return {
        'id': movement.id,
        'date': movement.created_at,
        'product': movement.product.name,
        'sku': movement.product.sku,
        'category': (
            movement.product.category.name
            if movement.product.category else None
        ),
        'movement_type': movement.movement_type,
        'movement_label': movement.get_movement_type_display(),
        'quantity': movement.quantity,
        'reason': movement.reason,
        'reference': movement.reference,
        'user': movement.created_by.username if movement.created_by else None,
    }


def movement_report(params):
    return [movement_row(movement) for movement in movement_queryset(params)]


def category_report(params=None):
    rows = []
    queryset = filtered_products(params or {})
    grouped = queryset.values('category_id', 'category__name').annotate(
        products=Count('id'),
        units=Coalesce(Sum('quantity'), Value(0)),
        value=Coalesce(
            Sum(F('quantity') * F('price')),
            Value(Decimal('0')),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
    ).order_by('-value', 'category__name')
    for row in grouped:
        rows.append({
            'category_id': row['category_id'],
            'category': row['category__name'] or 'Uncategorized',
            'products': row['products'],
            'units': row['units'],
            'value': row['value'],
        })
    return rows


def supplier_report(params=None):
    rows = []
    queryset = filtered_products(params or {})
    grouped = queryset.values('supplier_id', 'supplier__name').annotate(
        products=Count('id'),
        units=Coalesce(Sum('quantity'), Value(0)),
        value=Coalesce(
            Sum(F('quantity') * F('price')),
            Value(Decimal('0')),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
        low_stock=Count(
            'id',
            filter=Q(quantity__gt=0, quantity__lte=F('minimum_stock')),
        ),
        out_of_stock=Count('id', filter=Q(quantity=0)),
    ).order_by('-value', 'supplier__name')
    for row in grouped:
        rows.append({
            'supplier_id': row['supplier_id'],
            'supplier': row['supplier__name'] or 'No supplier',
            'products': row['products'],
            'units': row['units'],
            'value': row['value'],
            'low_stock': row['low_stock'],
            'out_of_stock': row['out_of_stock'],
        })
    return rows


def user_activity_report(params):
    queryset = movement_queryset(params)
    return list(queryset.values(
        'created_by_id', 'created_by__username'
    ).annotate(
        stock_in=Coalesce(Sum('quantity', filter=Q(movement_type='IN')), 0),
        stock_out=Coalesce(Sum('quantity', filter=Q(movement_type='OUT')), 0),
        adjustments=Coalesce(
            Sum('quantity', filter=Q(movement_type='ADJUSTMENT')), 0
        ),
        movements=Count('id'),
    ).order_by('-movements', 'created_by__username'))

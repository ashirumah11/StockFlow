import csv
from decimal import Decimal

from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import render

from inventory.models import Category, Product, Supplier

from .services import (
    category_report,
    current_stock_report,
    inventory_summary,
    movement_report,
    supplier_report,
    user_activity_report,
)


REPORTS = {
    'summary': ('Inventory summary', 'summary'),
    'current_stock': ('Current stock', 'products'),
    'low_stock': ('Low stock', 'products'),
    'out_of_stock': ('Out of stock', 'products'),
    'movements': ('Stock movements', 'movements'),
    'stock_in': ('Stock in', 'movements'),
    'stock_out': ('Stock out', 'movements'),
    'adjustments': ('Stock adjustments', 'movements'),
    'valuation': ('Inventory valuation', 'products'),
    'categories': ('Category report', 'categories'),
    'suppliers': ('Supplier report', 'suppliers'),
    'user_activity': ('User activity', 'users'),
}

PRODUCT_COLUMNS = (
    ('sku', 'SKU'), ('product', 'Product'), ('category', 'Category'),
    ('supplier', 'Supplier'), ('quantity', 'Quantity'),
    ('minimum_stock', 'Minimum'), ('maximum_stock', 'Maximum'),
    ('status', 'Status'), ('unit_price', 'Unit price'),
    ('stock_value', 'Stock value'),
)
MOVEMENT_COLUMNS = (
    ('date', 'Date'), ('product', 'Product'), ('sku', 'SKU'),
    ('movement_label', 'Type'), ('quantity', 'Quantity'),
    ('reason', 'Reason'), ('reference', 'Reference'), ('user', 'User'),
)
CATEGORY_COLUMNS = (
    ('category', 'Category'), ('products', 'Products'), ('units', 'Units'),
    ('value', 'Value'),
)
SUPPLIER_COLUMNS = (
    ('supplier', 'Supplier'), ('products', 'Products'), ('units', 'Units'),
    ('value', 'Value'), ('low_stock', 'Low stock'), ('out_of_stock', 'Out'),
)
USER_COLUMNS = (
    ('created_by__username', 'User'), ('stock_in', 'Stock in'),
    ('stock_out', 'Stock out'), ('adjustments', 'Adjustments'),
    ('movements', 'Movements'),
)


def report_params(request):
    params = {}
    for key in ('start_date', 'end_date', 'product', 'category', 'supplier', 'user'):
        if request.GET.get(key):
            params[key] = request.GET[key]
    return params


def summary_rows(summary):
    return [
        {'metric': 'Total products', 'value': summary['total_products']},
        {'metric': 'Total units', 'value': summary['total_units']},
        {'metric': 'Inventory value', 'value': summary['inventory_value']},
        {'metric': 'In-stock products', 'value': summary['in_stock_products']},
        {'metric': 'Low-stock products', 'value': summary['low_stock_products']},
        {'metric': 'Out-of-stock products', 'value': summary['out_of_stock_products']},
    ]


def report_data(report, params):
    if report == 'summary':
        return summary_rows(inventory_summary(params)), (('metric', 'Metric'), ('value', 'Value'))
    if report == 'current_stock':
        return current_stock_report(params), PRODUCT_COLUMNS
    if report == 'low_stock':
        return current_stock_report({**params, 'status': 'LOW_STOCK'}), PRODUCT_COLUMNS
    if report == 'out_of_stock':
        return current_stock_report({**params, 'status': 'OUT_OF_STOCK'}), PRODUCT_COLUMNS
    if report == 'valuation':
        return current_stock_report(params), PRODUCT_COLUMNS
    if report in {'movements', 'stock_in', 'stock_out', 'adjustments'}:
        movement_type = {
            'stock_in': 'IN',
            'stock_out': 'OUT',
            'adjustments': 'ADJUSTMENT',
        }.get(report)
        movement_params = {**params}
        if movement_type:
            movement_params['movement_type'] = movement_type
        return movement_report(movement_params), MOVEMENT_COLUMNS
    if report == 'categories':
        return category_report(params), CATEGORY_COLUMNS
    if report == 'suppliers':
        return supplier_report(params), SUPPLIER_COLUMNS
    return user_activity_report(params), USER_COLUMNS


def csv_response(title, columns, rows):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="stockflow-{title.lower().replace(" ", "-")}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow([label for key, label in columns])
    for row in rows:
        writer.writerow([row.get(key, '') for key, label in columns])
    return response


@admin.site.admin_view
def report_home(request):
    report = request.GET.get('report', 'summary')
    if report not in REPORTS:
        report = 'summary'
    params = report_params(request)
    if report in {'categories', 'suppliers', 'user_activity', 'valuation'}:
        role = getattr(getattr(request.user, 'profile', None), 'role', None)
        if not request.user.is_superuser and role not in {'ADMIN', 'MANAGER'}:
            messages.error(request, 'This report requires Manager or Admin access.')
            report = 'summary'

    try:
        rows, columns = report_data(report, params)
    except (ValueError, TypeError) as error:
        messages.error(request, str(error))
        rows, columns = report_data('summary', {})
        report = 'summary'

    if request.GET.get('export') == 'csv':
        return csv_response(REPORTS[report][0], columns, rows)

    context = {
        **admin.site.each_context(request),
        'title': 'Reports',
        'report': report,
        'report_title': REPORTS[report][0],
        'report_kind': REPORTS[report][1],
        'report_choices': [(key, value[0]) for key, value in REPORTS.items()],
        'columns': columns,
        'rows': rows,
        'display_rows': [
            [row.get(key) for key, label in columns]
            for row in rows
        ],
        'categories': Category.objects.order_by('name'),
        'suppliers': Supplier.objects.order_by('name'),
        'products': Product.objects.order_by('name'),
        'filters': params,
    }
    return render(request, 'admin/reports/index.html', context)

import csv

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes

from inventory.permissions import IsManagerOrAdmin

from .serializers import ReportQuerySerializer
from .services import (
    category_report,
    current_stock_report,
    inventory_summary,
    movement_report,
    supplier_report,
    user_activity_report,
)


class ReportView(APIView):
    permission_classes = [IsAuthenticated]

    def query_params(self, request, **defaults):
        params = request.query_params.copy()
        for key, value in defaults.items():
            params[key] = value
        serializer = ReportQuerySerializer(data=params)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data


class InventorySummaryReportView(ReportView):
    def get(self, request):
        params = self.query_params(request)
        return Response({
            'report': 'inventory_summary',
            'filters': params,
            'summary': inventory_summary(params),
        })


class CurrentStockReportView(ReportView):
    def get_permissions(self):
        if self.kwargs.get('report_type') == 'valuation':
            return [IsManagerOrAdmin()]
        return super().get_permissions()

    def get(self, request, **kwargs):
        params = self.query_params(request, **self.kwargs)
        rows = current_stock_report(params)
        if self.kwargs.get('status') == 'LOW_STOCK':
            name = 'low_stock'
        elif self.kwargs.get('status') == 'OUT_OF_STOCK':
            name = 'out_of_stock'
        elif request.path.endswith('/valuation/'):
            name = 'valuation'
        else:
            name = 'current_stock'
        return Response({
            'report': name,
            'filters': params,
            'count': len(rows),
            'results': rows,
        })


class MovementReportView(ReportView):
    def get(self, request, **kwargs):
        params = self.query_params(request, **self.kwargs)
        rows = movement_report(params)
        return Response({
            'report': self.kwargs.get('movement_type', 'all_movements').lower(),
            'filters': params,
            'count': len(rows),
            'results': rows,
        })


class CategoryReportView(ReportView):
    permission_classes = [IsManagerOrAdmin]

    def get(self, request):
        params = self.query_params(request)
        rows = category_report(params)
        return Response({
            'report': 'categories',
            'filters': params,
            'count': len(rows),
            'results': rows,
        })


class SupplierReportView(ReportView):
    permission_classes = [IsManagerOrAdmin]

    def get(self, request):
        params = self.query_params(request)
        rows = supplier_report(params)
        return Response({
            'report': 'suppliers',
            'filters': params,
            'count': len(rows),
            'results': rows,
        })


class UserActivityReportView(ReportView):
    permission_classes = [IsManagerOrAdmin]

    def get(self, request):
        params = self.query_params(request)
        rows = user_activity_report(params)
        return Response({
            'report': 'user_activity',
            'filters': params,
            'count': len(rows),
            'results': rows,
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_stock_csv(request):
    serializer = ReportQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    rows = current_stock_report(serializer.validated_data)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stock-report.csv"'
    writer = csv.writer(response)
    writer.writerow((
        'SKU', 'Product', 'Category', 'Supplier', 'Quantity',
        'Minimum Stock', 'Maximum Stock', 'Status', 'Unit Price', 'Stock Value',
    ))
    for row in rows:
        writer.writerow((
            row['sku'], row['product'], row['category'], row['supplier'],
            row['quantity'], row['minimum_stock'], row['maximum_stock'],
            row['status'], row['unit_price'], row['stock_value'],
        ))
    return response

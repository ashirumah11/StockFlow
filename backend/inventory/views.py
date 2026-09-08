from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdmin, IsManagerOrAdmin
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from .models import Product, Notification, StockMovement, Category, Supplier
from .serializers import (
    ProductSerializer,
    NotificationSerializer,
    StockMovementSerializer,
    CategorySerializer,
    SupplierSerializer,
)
from .services import create_stock_movement


def get_movement_analytics(period):
    periods = {'7d': 7, '30d': 30, '3m': 90, '12m': 365}
    days = periods.get(period, 7)
    today = timezone.localdate()
    start_date = today - timedelta(days=days - 1)

    movements = (
        StockMovement.objects
        .filter(created_at__date__gte=start_date)
        .annotate(day=TruncDate('created_at'))
        .values('day', 'movement_type')
        .annotate(total=Sum('quantity'))
    )
    totals = {
        (row['day'], row['movement_type']): row['total']
        for row in movements
    }

    return [
        {
            'date': (start_date + timedelta(days=offset)).isoformat(),
            'stock_in': totals.get((start_date + timedelta(days=offset), 'IN'), 0),
            'stock_out': totals.get((start_date + timedelta(days=offset), 'OUT'), 0),
            'adjustments': totals.get((start_date + timedelta(days=offset), 'ADJUSTMENT'), 0),
        }
        for offset in range(days)
    ]
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        'category',
        'supplier',
    ]

    search_fields = [
        'name',
        'sku',
    ]

    ordering_fields = [
        'name',
        'quantity',
        'price',
        'created_at',
        'updated_at',
    ]

    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()

        status_filter = self.request.query_params.get('status')

        if status_filter == 'LOW_STOCK':
            queryset = queryset.filter(
                quantity__gt=0,
                quantity__lte=models.F('minimum_stock')
            )

        elif status_filter == 'OUT_OF_STOCK':
            queryset = queryset.filter(quantity=0)

        elif status_filter == 'IN_STOCK':
            queryset = queryset.filter(
                quantity__gt=models.F('minimum_stock')
            )

        return queryset

    def get_permissions(self):
        if self.action in [
            'create',
            'update',
            'partial_update',
            'destroy',
        ]:
            return [IsManagerOrAdmin()]

        return [IsAuthenticated()]

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']

    def get_permissions(self):
        if self.action in [
            'create',
            'update',
            'partial_update',
            'destroy',
        ]:
            return [IsManagerOrAdmin()]

        return [IsAuthenticated()]

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by('name')
    serializer_class = SupplierSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'contact_person', 'email', 'phone']
    ordering_fields = ['name']

    def get_permissions(self):
        if self.action in [
            'create',
            'update',
            'partial_update',
            'destroy',
        ]:
            return [IsManagerOrAdmin()]

        return [IsAuthenticated()]

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.all()
        category_snapshot = Category.objects.annotate(
            total_items=Count('products'),
            total_quantity=Sum('products__quantity'),
        ).values('id', 'name', 'total_items', 'total_quantity')

        recent_alerts = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).select_related('product').order_by('-created_at')[:5]

        recent_movements = StockMovement.objects.select_related(
            'product',
            'created_by',
        ).order_by('-created_at')
        movement_type = request.query_params.get('movement_type')
        if movement_type in {'IN', 'OUT', 'ADJUSTMENT'}:
            recent_movements = recent_movements.filter(
                movement_type=movement_type
            )

        low_stock_products = products.filter(
            quantity__lte=models.F('minimum_stock')
        ).order_by('quantity', 'name')[:5]
        top_products = products.order_by('-quantity', 'name')[:5]

        return Response({
            'health_tiles': {
                'total_products': products.count(),
                'total_stock': sum(
                    product.quantity for product in products
                ),
                'in_stock': products.filter(
                    quantity__gt=models.F('minimum_stock')
                ).count(),
                'low_stock': products.filter(
                    quantity__gt=0,
                    quantity__lte=models.F('minimum_stock'),
                ).count(),
                'out_of_stock': products.filter(quantity=0).count(),
            },
            'inventory_snapshot': list(category_snapshot),
            'low_stock_products': ProductSerializer(
                low_stock_products,
                many=True,
            ).data,
            'top_products': ProductSerializer(
                top_products,
                many=True,
            ).data,
            'alerts': NotificationSerializer(
                recent_alerts,
                many=True,
            ).data,
            'recent_movements': StockMovementSerializer(
                recent_movements[:6],
                many=True
            ).data,
            'movement_analytics': get_movement_analytics(
                request.query_params.get('period', '7d')
            ),
        })


class InventoryReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.select_related('category', 'supplier')
        return Response({
            'generated_at': timezone.now(),
            'summary': {
                'total_products': products.count(),
                'total_stock': sum(product.quantity for product in products),
                'inventory_value': sum(
                    product.quantity * product.price for product in products
                ),
                'low_stock': products.filter(
                    quantity__gt=0,
                    quantity__lte=models.F('minimum_stock'),
                ).count(),
                'out_of_stock': products.filter(quantity=0).count(),
            },
            'products': ProductSerializer(products, many=True).data,
        })


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all().order_by('-created_at')
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product', 'movement_type', 'created_by']
    search_fields = ['product__name', 'product__sku', 'reason']
    ordering_fields = ['created_at', 'quantity', 'movement_type']

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdmin()]

        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        movement = create_stock_movement(
            product=serializer.validated_data['product'],
            movement_type=serializer.validated_data['movement_type'],
            quantity=serializer.validated_data['quantity'],
            reason=serializer.validated_data.get('reason', ''),
            reference=serializer.validated_data.get('reference', ''),
            user=request.user
        )

        output_serializer = self.get_serializer(movement)
        response_data = output_serializer.data
        response_data['message'] = (
            f'Stock {movement.get_movement_type_display().lower()} completed '
            f'for {movement.product.name}. '
            f'Current quantity: {movement.product.quantity}.'
        )

        return Response(
            response_data,
            status=status.HTTP_201_CREATED
        )


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
        notification_type = self.request.query_params.get('type')
        is_read = self.request.query_params.get('is_read')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        if is_read in {'true', 'false'}:
            queryset = queryset.filter(is_read=is_read == 'true')
        return queryset

    @action(detail=True, methods=['patch'], url_path='read')
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()

        notification.is_read = True
        notification.save(update_fields=['is_read'])

        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK
        )
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        count = self.get_queryset().filter(
            is_read=False
        ).count()

        return Response({
            'unread_count': count
        })

    @action(detail=False, methods=['patch'], url_path='read-all')
    def mark_all_as_read(self, request):
        self.get_queryset().filter(
            is_read=False
        ).update(is_read=True)

        return Response({
            'message': 'All notifications marked as read.'
        }, status=status.HTTP_200_OK)

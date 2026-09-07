from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdmin, IsManagerOrAdmin
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.db.models import Count, Sum

from .models import Product, Notification, StockMovement, Category, Supplier
from .serializers import (
    ProductSerializer,
    NotificationSerializer,
    StockMovementSerializer,
    CategorySerializer,
    SupplierSerializer,
)
from .services import create_stock_movement
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
        })


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.all().order_by('-created_at')
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
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
            user=request.user
        )

        output_serializer = self.get_serializer(movement)

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

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

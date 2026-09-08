from rest_framework import serializers
from .models import Product, Notification, StockMovement, Category, Supplier


class ProductSerializer(serializers.ModelSerializer):
    stock_status = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'sku', 'image_url', 'category', 'supplier', 'quantity',
            'minimum_stock', 'maximum_stock', 'price', 'stock_status',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'stock_status', 'created_at', 'updated_at')

    def validate(self, attrs):
        minimum_stock = attrs.get('minimum_stock', getattr(self.instance, 'minimum_stock', None))
        maximum_stock = attrs.get('maximum_stock', getattr(self.instance, 'maximum_stock', None))
        quantity = attrs.get('quantity', getattr(self.instance, 'quantity', 0))

        if minimum_stock is not None and maximum_stock is not None and minimum_stock > maximum_stock:
            raise serializers.ValidationError('Minimum stock cannot exceed maximum stock.')
        if maximum_stock is not None and quantity > maximum_stock:
            raise serializers.ValidationError('Quantity cannot exceed maximum stock.')
        return attrs


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description')
        read_only_fields = ('id',)

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ('id', 'name', 'contact_person', 'phone', 'email', 'address')
        read_only_fields = ('id',)


class NotificationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Notification
        fields = (
            'id',
            'product',
            'product_name',
            'user',
            'title',
            'message',
            'notification_type',
            'is_read',
            'created_at',
        )
        read_only_fields = (
            'user',
            'title',
            'message',
            'notification_type',
            'created_at',
        )


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = StockMovement
        fields = (
            'id',
            'product',
            'product_name',
            'movement_type',
            'quantity',
            'reason',
            'reference',
            'created_by',
            'created_by_name',
            'created_at',
        )
        read_only_fields = (
            'created_by',
            'created_at',
        )

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than zero.')
        return value

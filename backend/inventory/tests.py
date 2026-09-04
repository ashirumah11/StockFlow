from django.contrib.auth.models import User
from django.test import TestCase

from inventory.models import Product, Notification, StockMovement
from inventory.services import create_stock_movement

class StockMovementTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='manager_test',
            password='testpass123'
        )
        # Update the auto-created profile to have a manager role
        self.user.profile.role = 'MANAGER'
        self.user.profile.save()

        self.product = Product.objects.create(
            name='Test Laptop',
            sku='TEST-LAP-001',
            quantity=15,
            minimum_stock=10,
            maximum_stock=100,
            price=75000
        )

    def test_stock_in_updates_quantity(self):
        create_stock_movement(
            product=self.product,
            movement_type='IN',
            quantity=5,
            reason='Test stock in',
            user=self.user
        )

        self.product.refresh_from_db()

        self.assertEqual(self.product.quantity, 20)

    def test_stock_out_updates_quantity(self):
        create_stock_movement(
            product=self.product,
            movement_type='OUT',
            quantity=5,
            reason='Test stock out',
            user=self.user
        )

        self.product.refresh_from_db()

        self.assertEqual(self.product.quantity, 10)

    def test_low_stock_notification_is_created(self):
        create_stock_movement(
            product=self.product,
            movement_type='OUT',
            quantity=6,
            reason='Trigger low stock',
            user=self.user
        )

        self.assertTrue(
            Notification.objects.filter(
                product=self.product,
                notification_type='LOW_STOCK'
            ).exists()
        )

    def test_stock_movement_records_user(self):
        movement = create_stock_movement(
            product=self.product,
            movement_type='IN',
            quantity=5,
            reason='User tracking test',
            user=self.user
        )

        self.assertEqual(movement.created_by, self.user)

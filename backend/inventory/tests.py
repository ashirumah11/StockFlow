from django.contrib.auth.models import User
from rest_framework.test import APIClient
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

    def test_stock_movement_creates_completion_notification(self):
        create_stock_movement(
            product=self.product,
            movement_type='IN',
            quantity=5,
            reason='Completion notification test',
            user=self.user,
        )

        notification = Notification.objects.get(
            user=self.user,
            notification_type='STOCK_MOVEMENT',
        )
        self.assertIn('Stock in completed', notification.title)
        self.assertIn('Current quantity: 20', notification.message)


class InventoryApiTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='api_user',
            password='testpass123',
        )
        self.user.profile.role = 'MANAGER'
        self.user.profile.save()
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.product = Product.objects.create(
            name='API Product',
            sku='API-001',
            quantity=5,
            minimum_stock=10,
            maximum_stock=100,
            price=12.50,
        )

    def test_dashboard_returns_requested_analytics_period(self):
        response = self.client.get('/api/dashboard/?period=7d')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['movement_analytics']), 7)
        self.assertIn('low_stock_products', response.data)

    def test_inventory_report_returns_summary(self):
        response = self.client.get('/api/reports/inventory/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['total_products'], 1)
        self.assertEqual(response.data['summary']['low_stock'], 1)

    def test_stock_movement_accepts_reference(self):
        response = self.client.post('/api/stock-movements/', {
            'product': self.product.id,
            'movement_type': 'IN',
            'quantity': 3,
            'reason': 'Supplier delivery',
            'reference': 'INV-2026-0012',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['reference'], 'INV-2026-0012')
        self.assertIn('completed', response.data['message'])

    def test_stock_movement_cannot_be_updated_or_deleted(self):
        movement = create_stock_movement(
            product=self.product,
            movement_type='IN',
            quantity=3,
            user=self.user,
        )
        admin_user = User.objects.create_superuser(
            username='movement_admin',
            password='testpass123',
        )
        admin_user.profile.role = 'ADMIN'
        admin_user.profile.save()
        self.client.force_authenticate(admin_user)

        detail_url = f'/api/stock-movements/{movement.id}/'
        update_response = self.client.patch(
            detail_url,
            {'quantity': 99},
            format='json',
        )
        delete_response = self.client.delete(detail_url)

        self.assertEqual(update_response.status_code, 405)
        self.assertEqual(delete_response.status_code, 405)

    def test_notifications_can_filter_by_read_state(self):
        Notification.objects.create(
            user=self.user,
            product=self.product,
            title='Low stock',
            message='Review this product',
            notification_type='LOW_STOCK',
        )

        response = self.client.get('/api/notifications/?type=LOW_STOCK&is_read=false')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)

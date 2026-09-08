from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APITestCase

from inventory.models import Category, Product, StockMovement, Supplier
from inventory.services import create_stock_movement


class ReportApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='report_manager', password='testpass123'
        )
        self.user.profile.role = 'MANAGER'
        self.user.profile.save()
        self.client.force_authenticate(self.user)
        self.category = Category.objects.create(name='Hardware')
        self.supplier = Supplier.objects.create(name='Acme Supply')
        self.product = Product.objects.create(
            name='Keyboard', sku='KB-001', category=self.category,
            supplier=self.supplier, quantity=4, minimum_stock=10,
            maximum_stock=100, price=Decimal('25.00'),
        )
        self.out_product = Product.objects.create(
            name='Monitor', sku='MON-001', category=self.category,
            quantity=0, minimum_stock=5, maximum_stock=20,
            price=Decimal('100.00'),
        )
        create_stock_movement(
            product=self.product, movement_type='IN', quantity=4, user=self.user
        )

    def test_summary_contains_inventory_kpis(self):
        response = self.client.get('/api/reports/summary/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['total_products'], 2)
        self.assertEqual(response.data['summary']['total_units'], 8)
        self.assertEqual(response.data['summary']['inventory_value'], Decimal('200.00'))
        self.assertEqual(response.data['summary']['out_of_stock_products'], 1)

    def test_low_stock_report_supports_status_filter(self):
        response = self.client.get('/api/reports/low-stock/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['sku'], 'KB-001')

    def test_movement_report_supports_type_filter(self):
        response = self.client.get('/api/reports/stock-in/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['movement_type'], 'IN')

    def test_current_stock_can_export_csv(self):
        response = self.client.get('/api/reports/current-stock/export/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('KB-001', response.content.decode())

    def test_management_reports_require_manager_or_admin(self):
        self.user.profile.role = 'STAFF'
        self.user.profile.save()

        response = self.client.get('/api/reports/categories/')

        self.assertEqual(response.status_code, 403)


class AdminReportPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin_report_user',
            password='testpass123',
            is_staff=True,
        )
        self.user.profile.role = 'MANAGER'
        self.user.profile.save()
        self.client.force_login(self.user)
        Product.objects.create(
            name='Admin Report Product',
            sku='ADMIN-001',
            quantity=3,
            minimum_stock=5,
            maximum_stock=20,
            price=Decimal('15.00'),
        )

    def test_admin_report_generator_renders_results(self):
        response = self.client.get('/admin/reports/?report=low_stock')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Report Product')
        self.assertContains(response, 'Low stock')

    def test_admin_report_generator_exports_csv(self):
        response = self.client.get(
            '/admin/reports/?report=current_stock&export=csv'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('ADMIN-001', response.content.decode())

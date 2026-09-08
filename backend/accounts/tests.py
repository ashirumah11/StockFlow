from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient


class UserManagementApiTests(TestCase):

	def setUp(self):
		self.admin = User.objects.create_user(
			username='api_admin',
			password='testpass123',
		)
		self.admin.profile.role = 'ADMIN'
		self.admin.profile.save()
		self.client = APIClient()

	def test_admin_can_create_managed_user(self):
		self.client.force_authenticate(self.admin)

		response = self.client.post('/api/auth/users/', {
			'username': 'managed_user',
			'email': 'managed@example.com',
			'password': 'testpass123',
			'role': 'STAFF',
		}, format='json')

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data['role'], 'STAFF')

	def test_non_admin_cannot_list_managed_users(self):
		staff = User.objects.create_user(
			username='api_staff',
			password='testpass123',
		)
		self.client.force_authenticate(staff)

		response = self.client.get('/api/auth/users/')

		self.assertEqual(response.status_code, 403)

# Create your tests here.

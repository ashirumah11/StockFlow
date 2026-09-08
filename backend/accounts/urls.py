from django.urls import path

from .views import (
    RegisterView,
    MeView,
    UserManagementView,
    ManagedUserDetailView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', MeView.as_view(), name='me'),
    path('users/', UserManagementView.as_view(), name='user-list'),
    path('users/<int:pk>/', ManagedUserDetailView.as_view(), name='user-detail'),
]

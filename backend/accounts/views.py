from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from inventory.permissions import IsAdmin

from .serializers import UserSerializer, RegisterSerializer, UserManagementSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserManagementView(generics.ListCreateAPIView):
    queryset = User.objects.select_related('profile').order_by('username')
    serializer_class = UserManagementSerializer
    permission_classes = [IsAdmin]


class ManagedUserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.select_related('profile')
    serializer_class = UserManagementSerializer
    permission_classes = [IsAdmin]


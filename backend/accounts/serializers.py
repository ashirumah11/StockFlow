from django.contrib.auth.models import User
from rest_framework import serializers

from inventory.models import UserProfile

class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
        )

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        default='STAFF',
        write_only=True
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'role',
        )

    def create(self, validated_data):
        role = validated_data.pop('role', 'STAFF')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        # Update the auto-created profile from the signal
        user.profile.role = role
        user.profile.save()

        return user


class UserManagementSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        source='profile.role',
    )
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'is_active',
            'last_login',
            'password',
        )
        read_only_fields = ('id', 'last_login')

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'password': 'This field is required.'})

        user = User.objects.create_user(password=password, **validated_data)
        if 'role' in profile_data:
            user.profile.role = profile_data['role']
            user.profile.save(update_fields=['role'])
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save(update_fields=['password'])
        if 'role' in profile_data:
            user.profile.role = profile_data['role']
            user.profile.save(update_fields=['role'])
        return user

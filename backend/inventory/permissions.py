from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, 'profile')
            and request.user.profile.role == 'ADMIN'
        )


class IsManagerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'profile'):
            return False

        return request.user.profile.role in ['ADMIN', 'MANAGER']


class IsStaffOrAbove(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if not hasattr(request.user, 'profile'):
            return False

        return request.user.profile.role in [
            'ADMIN',
            'MANAGER',
            'STAFF',
        ]

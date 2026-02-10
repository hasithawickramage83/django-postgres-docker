from rest_framework import permissions

class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only admin users to edit products.
    Everyone else can only read (GET).
    """

    def has_permission(self, request, view):
        # SAFE_METHODS = GET, HEAD, OPTIONS
        if request.method in permissions.SAFE_METHODS:
            return True
        # Only admin users (is_staff=True) can POST, PUT, DELETE
        return request.user and request.user.is_staff

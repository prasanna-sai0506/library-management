from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access (GET, HEAD, OPTIONS) to authenticated users.
    Mutations (POST, PUT, PATCH, DELETE) require ADMIN or staff status.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_staff or request.user.role == request.user.ADMIN:
            return True

        return False

class IsAdminOnly(permissions.BasePermission):
    """
    Allows access strictly to Admins or superusers.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser or request.user.role == request.user.ADMIN:
            return True

        return False

class IsAdminOrOwner(permissions.BasePermission):
    """
    Allows general access to authenticated users, but object-level permissions 
    restrict modifications/views to the record owner or admins.
    """
    def has_permission(self, request, view): 
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.role == request.user.ADMIN:
            return True
        # Assumes the target model object has a `.user` foreign key attribute
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        return False
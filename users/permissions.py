from rest_framework import permissions

def is_library_staff(user):
    return bool(
        user
        and user.is_authenticated
        and (
            user.is_staff
            or user.is_superuser
            or user.role == user.LIBRARIAN
        )
    )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access (GET, HEAD, OPTIONS) to authenticated users.
    Mutations (POST, PUT, PATCH, DELETE) require librarian or staff status.
    """
    def has_permission(self, request, view):       
        if not request.user or not request.user.is_authenticated:  
            return False
     
        if request.method in permissions.SAFE_METHODS:    
            return True

        if is_library_staff(request.user):
            return True

        return False

class IsLibrarianOnly(permissions.BasePermission):
    """
    Allows access strictly to librarians or staff users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if is_library_staff(request.user):
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
        if is_library_staff(request.user):
            return True
        # Assumes the target model object has a `.user` foreign key attribute
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        return False
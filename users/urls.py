# users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    UserProfileView,
    AdminCreateLibrarianView,
    AdminUserListView,
    AdminUserDetailView,
    AdminUserBorrowingsView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('create-admin/', AdminCreateLibrarianView.as_view(), name='create-admin'),
    path('users-list/', AdminUserListView.as_view(), name='admin-user-list'),
    path('users-list/<int:user_id>/borrowings/', AdminUserBorrowingsView.as_view(), name='admin-user-borrowings'),
    path('users-list/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
]
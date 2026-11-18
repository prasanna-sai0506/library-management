"""
URL configuration for librarymanagement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from borrowings.views import BorrowingListCreateAPIView, BorrowingReturnAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('users/', include('users.urls')),
    path('library/', include('books.urls')),
    path('borrowings/', BorrowingListCreateAPIView.as_view(), name='borrowing-list-create'),
    path('borrowings/return/', BorrowingReturnAPIView.as_view(), name='borrowing-return'),
]

if settings.DEBUG:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
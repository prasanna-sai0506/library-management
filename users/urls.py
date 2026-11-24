from django.urls import path
from .views import RegisterView,UserProfileView,LibrarianCreateView,UserListAPIView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('create-librarian/', LibrarianCreateView.as_view(), name='create-librarian'),
    path('userslist/', UserListAPIView.as_view(), name='user-list'),
]

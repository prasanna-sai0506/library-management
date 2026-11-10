# users/views.py
from rest_framework import generics, permissions
from .models import User
from .serializers import UserRegistrationSerializer, UserSerializer
from .permissions import IsAdminOnly


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AdminCreateLibrarianView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsAdminOnly]

    def perform_create(self, serializer):
        serializer.save(role=User.ADMIN)
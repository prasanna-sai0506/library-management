# users/views.py
from rest_framework import generics, permissions
from .models import User
from .serializers import UserRegistrationSerializer, UserSerializer
from .permissions import IsAdminOnly
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer


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


class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [IsAdminOnly]


class AdminUserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOnly]


class AdminUserBorrowingsView(generics.ListAPIView):
    serializer_class = BorrowingSerializer
    permission_classes = [IsAdminOnly]

    def get_queryset(self):
        return Borrowing.objects.filter(
            user_id=self.kwargs['user_id']
        ).select_related('user', 'book').order_by('-borrowed_at')
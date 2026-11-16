from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .permissions import IsLibrarianOnly
from librarymanagement.pagination import DefaultPagination
from .serializers import (
    UserProfileSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class LibrarianCreateView(APIView):
    permission_classes = [IsLibrarianOnly]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(role=User.LIBRARIAN)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class LibrarianUserListView(APIView):
    permission_classes = [IsLibrarianOnly]

    def get(self, request):
        user_id = request.query_params.get('id')
        users = User.objects.all().order_by('username')
        if user_id:
            users = users.filter(id=user_id)
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(users, request, view=self)
        return paginator.get_paginated_response(UserSerializer(page, many=True).data)


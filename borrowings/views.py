from django.db.models import F
from rest_framework import generics, status, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Borrowing
from books.models import Book
from .serializers import BorrowingSerializer
from users.permissions import IsAdminOnly, IsAdminOrOwner


class BorrowingListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = BorrowingSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['book__title', 'user__username']
    ordering_fields = ['borrowed_at', 'due_date', 'returned_at']
    ordering = ['-borrowed_at']
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == user.ADMIN:
            return Borrowing.objects.all()
        return Borrowing.objects.filter(user=user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        book_id = request.data.get('book')
        user = request.user

        if user.role != user.MEMBER or user.is_staff:
            return Response({"error": "Only members can borrow books."}, status=status.HTTP_403_FORBIDDEN)

        book = get_object_or_404(Book, id=book_id)

        if book.available_copies <= 0 or book.availability == "UNAVAILABLE":
            return Response({"error": "No copies available for this book."}, status=status.HTTP_400_BAD_REQUEST)

        user_credits = Decimal(str(user.credits))
        borrowing_cost = Decimal(str(book.borrowing_cost))

        if user_credits < borrowing_cost:
            return Response({"error": "Insufficient credits to borrow this book."}, status=status.HTTP_400_BAD_REQUEST)

        user.credits = user_credits - borrowing_cost
        user.save()

        book.available_copies -= 1
        if book.available_copies == 0:
            book.availability = "UNAVAILABLE"
        book.save()
        due_date = timezone.now() + timedelta(days=book.borrowing_period)
        
        borrowing = Borrowing.objects.create(
            user=user,book=book,\
            credits_spent=book.borrowing_cost,\
            borrowing_period=book.borrowing_period,\
            due_date=due_date,\
            status=Borrowing.BORROWED\
        )

        serializer = self.get_serializer(borrowing)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
class BorrowingDetailAPIView(generics.RetrieveAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
class BorrowingReturnAPIView(generics.GenericAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOnly]

    @transaction.atomic
    def post(self, request, pk=None):
        borrowing = get_object_or_404(Borrowing, pk=pk)
        self.check_object_permissions(request, borrowing)  #check the borrowing belongs to the login user

        if borrowing.status == Borrowing.RETURNED:
            return Response({"error": "This book has already been returned."}, status=status.HTTP_400_BAD_REQUEST)

        return_time = timezone.now()      # Calculate late fee & update borrowing record
        late_fee = borrowing.calculate_late_fee(return_time)
        borrowing.returned_at = return_time
        borrowing.late_fee = late_fee
        borrowing.status = Borrowing.RETURNED
        borrowing.save()
        Book.objects.filter(pk=borrowing.book.pk).update(available_copies=F('available_copies') + 1) # increment copies
        Book.objects.filter(pk=borrowing.book.pk, available_copies__gt=0).update(availability=Book.AVAILABLE) # update available copies

        if late_fee > 0:           # Deduct late fee from user credits if applicable
            borrowing.user.credits -= late_fee
            borrowing.user.save()

        serializer = self.get_serializer(borrowing)
        return Response({
            "message": "Book returned successfully.",\
            "late_fee_charged": str(late_fee),\
            "borrowing": serializer.data\
        }, status=status.HTTP_200_OK)
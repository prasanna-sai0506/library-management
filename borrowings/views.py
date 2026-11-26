from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from books.models import AVAILABLE, Book
from librarymanagement.pagination import DefaultPagination
from users.permissions import IsLibrarianOnly, is_library_staff
from .models import Borrowing, UnderDeskBook
from .serializers import BorrowingCreateSerializer, BorrowingSerializer


class BorrowingListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        borrowings = Borrowing.objects.select_related("user", "book")
        if not is_library_staff(request.user):
            borrowings = borrowings.filter(user=request.user)

        borrowing_id = request.query_params.get("id")
        user_id = request.query_params.get("user_id")
        status_filter = request.query_params.get("status")
        search = request.query_params.get("search")
        if borrowing_id:
            borrowings = borrowings.filter(id=borrowing_id)
        if user_id and is_library_staff(request.user):
            borrowings = borrowings.filter(user_id=user_id)
        if status_filter:
            borrowings = borrowings.filter(status=status_filter)
        if search:
            borrowings = borrowings.filter(
                Q(book__title__icontains=search) | Q(user__username__icontains=search)
            )

        ordering = request.query_params.get("ordering", "-borrowed_at")
        allowed_ordering = {"borrowed_at", "due_date", "returned_at"}
        ordering_fields = [
            field
            for field in ordering.split(",")
            if field.lstrip("-") in allowed_ordering
        ]
        borrowings = borrowings.order_by(*(ordering_fields or ["-borrowed_at"]))
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(borrowings, request, view=self)
        return paginator.get_paginated_response(
            borrowing_data(page, request, many=True)
        )

    def post(self, request):
        serializer = BorrowingCreateSerializer(
            data=request.data, context={"request": request}
        )
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as exc:
            book_errors = (
                exc.detail.get("book") if isinstance(exc.detail, dict) else None
            )
            if book_errors:
                return Response(
                    {"error": str(book_errors[0])}, status=status.HTTP_400_BAD_REQUEST
                )
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        try:
            borrowing = serializer.save()
        except serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            borrowing_data(borrowing, request), status=status.HTTP_201_CREATED
        )


class BorrowingReturnAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsLibrarianOnly]

    def post(self, request):
        borrowing = get_borrowing_from_query(request)
        with transaction.atomic():
            if isinstance(borrowing, Response):
                return borrowing
            self.check_object_permissions(request, borrowing)
            if borrowing.status == Borrowing.RETURNED:
                return Response(
                    {"error": "This book has already been returned."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return_time = timezone.now()
            late_fee = borrowing.calculate_late_fee(return_time)
            borrowing.returned_at = return_time
            borrowing.late_fee = late_fee
            borrowing.status = Borrowing.RETURNED
            borrowing.save()
            Book.objects.filter(pk=borrowing.book_id).update(
                available_copies=F("available_copies") + 1
            )
            Book.objects.filter(pk=borrowing.book_id, available_copies__gt=0).update(
                availability=AVAILABLE
            )
            UnderDeskBook.objects.get_or_create(
                borrowing=borrowing,
                defaults={"book": borrowing.book},
            )

            if late_fee > 0:
                borrowing.user.credits -= late_fee
                borrowing.user.save()

            return Response(
                {
                    "message": "Book returned successfully.",
                    "late_fee_charged": str(late_fee),
                    "borrowing": borrowing_data(borrowing, request),
                }
            )


class UnderDeskCloseAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsLibrarianOnly]

    def post(self, request):
        with transaction.atomic():
            under_desk_count = UnderDeskBook.objects.select_for_update().count()
            UnderDeskBook.objects.all().delete()

        return Response(
            {
                "message": f"{under_desk_count} under-desk book(s) moved to the shelf.",
                "moved_count": under_desk_count,
            }
        )


class UnderDeskListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsLibrarianOnly]

    def get(self, request):
        copies = UnderDeskBook.objects.select_related(
            "book",
            "borrowing",
            "borrowing__user",
        ).order_by("placed_at")

        paginator = DefaultPagination()
        page = paginator.paginate_queryset(copies, request, view=self)
        data = [
            {
                "id": copy.id,
                "book": copy.book_id,
                "title": copy.book.title,
                "isbn": copy.book.isbn,
                "borrower": copy.borrowing.user.username,
                "borrowing": copy.borrowing_id,
                "placed_at": copy.placed_at,
            }
            for copy in page
        ]
        return paginator.get_paginated_response(data)


def get_borrowing_from_query(request):
    borrowing_id = request.query_params.get("id")
    if not borrowing_id:
        return Response(
            {"error": "The id query parameter is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return get_object_or_404(Borrowing, id=borrowing_id)


def borrowing_data(borrowings, request, many=False):
    return BorrowingSerializer(borrowings, many=many, context={"request": request}).data

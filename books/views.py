from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdminOrReadOnly, is_library_staff

from .models import Book
from .serializers import BookMemberSerializer, BookSerializer


class BookAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]
    allowed_ordering_fields = { 'borrowing_cost','total_copies','title','borrowing_period'}

    def get(self, request):
        book_id = request.query_params.get('id')
        if book_id:
            book = self.get_book(book_id)
            if isinstance(book, Response):
                return book
            return Response(self.book_data(book, request))

        books = Book.objects.all()
        category = request.query_params.get('category')
        availability = request.query_params.get('availability')
        search = request.query_params.get('search')
        name = request.query_params.get('name')
        ordering = request.query_params.get('ordering', 'title')

        if category:
            books = books.filter(category=category)
        if availability:
            books = books.filter(availability=availability)
        if search:
            books = books.filter(
                Q(title__icontains=search)
                | Q(author__icontains=search)
                | Q(isbn__icontains=search)
            )
        if name:
            books = books.filter(title__icontains=name)

        ordering_fields = [
            field for field in ordering.split(',')
            if field.lstrip('-') in self.allowed_ordering_fields
        ]
        books = books.order_by(*(ordering_fields or ['title']))

        return Response([
            self.book_data(book, request) for book in books
        ])

    def post(self, request):
        serializer = BookSerializer(
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        total_copies = serializer.validated_data.get('total_copies', 1)
        serializer.save(
            available_copies=total_copies,
            availability=(
                Book.AVAILABLE if total_copies > 0 else Book.UNAVAILABLE
            ),
        )
        return Response(self.book_data(serializer.instance, request),status=status.HTTP_201_CREATED)

    def put(self, request):
        book = self.get_book_from_request(request)
        
        if isinstance(book, Response):
            return book

        serializer = BookSerializer(book,data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self.book_data(serializer.instance, request))

    def patch(self, request):
        book = self.get_book_from_request(request)
        
        if isinstance(book, Response):
            return book

        serializer = BookSerializer(book,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self.book_data(serializer.instance, request))

    def delete(self, request):
        book = self.get_book_from_request(request)
        
        if isinstance(book, Response):
            return book
        
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_book_from_request(self, request):
        book_id = request.query_params.get('id')
        if not book_id:
            return Response({'error': 'The id query parameter is required.'},status=status.HTTP_400_BAD_REQUEST)
        return self.get_book(book_id)

    def get_book(self, book_id):
        try:
            book_id = int(book_id)
        except (TypeError, ValueError):
            return Response({'error': 'The book id must be an integer.'},status=status.HTTP_400_BAD_REQUEST)
        return get_object_or_404(Book, id=book_id)

    @staticmethod
    def book_data(book, request):
        if is_library_staff(request.user):
            serializer_class = (BookSerializer)
        else:
            serializer_class = (BookMemberSerializer)
    
        return serializer_class(book).data

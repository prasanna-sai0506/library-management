from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsAdminOrReadOnly, is_library_staff
from librarymanagement.pagination import DefaultPagination
from django.db import transaction
from django.db.models import IntegerField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from .models import AVAILABLE, UNAVAILABLE, Book, Shelf
from .serializers import BookMemberSerializer, BookSerializer, ShelfSerializer

class ShelfAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = DefaultPagination

    def get(self, request):
        shelf_id = request.query_params.get('id')
        book_copy_totals = Book.objects.filter(shelf_id=OuterRef('pk')).order_by()\
            .values('shelf_id').annotate(total=Sum('total_copies')).values('total')
        shelves = Shelf.objects.annotate(
            _assigned_book_copies=Coalesce(
                Subquery(book_copy_totals, output_field=IntegerField()), Value(0)
            )
        ).order_by('column_name', 'shelf_number')
        if shelf_id:
            try:
                shelf_id = int(shelf_id)
            except (TypeError, ValueError):
                return Response({'error': 'The shelf id must be an integer.'},
                                status=status.HTTP_400_BAD_REQUEST)
            shelf = get_object_or_404(Shelf, id=shelf_id)
            return Response(ShelfSerializer(shelf).data)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(shelves, request, view=self)
        self.paginator = paginator
        return paginator.get_paginated_response(ShelfSerializer(page, many=True).data)

    def post(self, request):
        if request.path.rstrip('/').endswith('/pack'):
            return self.pack_books()
        serializer = ShelfSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()   
        except serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        shelf_id = request.query_params.get('id')
        if not shelf_id:
            return Response({'error': 'The id query parameter is required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            shelf_id = int(shelf_id)
        except (TypeError, ValueError):
            return Response({'error': 'The shelf id must be an integer.'},
                            status=status.HTTP_400_BAD_REQUEST)
        shelf = get_object_or_404(Shelf, id=shelf_id)
        assigned = ShelfSerializer(shelf).get_assigned_copies(shelf)
        serializer = ShelfSerializer(shelf, data=request.data, partial=True)
        if 'capacity' in request.data:
            try:
                capacity = int(request.data['capacity'])
            except (TypeError, ValueError):
                return Response({'error': 'Capacity must be an integer.'},
                                status=status.HTTP_400_BAD_REQUEST)
            if capacity < assigned:
                return Response({'error': 'Capacity cannot be lower than assigned copies.'},
                                status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)

    def delete(self, request):
        shelf_id = request.query_params.get('id')
        if not shelf_id:
            return Response({'error': 'The id query parameter is required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            shelf_id = int(shelf_id)
        except (TypeError, ValueError):
            return Response({'error': 'The shelf id must be an integer.'},
                            status=status.HTTP_400_BAD_REQUEST)
        shelf = get_object_or_404(Shelf, id=shelf_id)
        if ShelfSerializer(shelf).get_assigned_copies(shelf) or shelf.books.exists():
            return Response({'error': 'Shelf has assigned books.'},
                            status=status.HTTP_409_CONFLICT)
        shelf.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def pack_books(self):
        with transaction.atomic():
            shelves = list(Shelf.objects.select_for_update().order_by('column_name', 'shelf_number'))
            books = list(Book.objects.select_for_update().order_by('pk'))
            if not shelves and books:
                return Response({'error': 'Create at least one shelf before arranging books.'}, status=400)
            placements = {shelf.pk: {} for shelf in shelves}
            book_locations = {book.pk: [] for book in books}
            shelf_index = 0
            remaining = shelves[0].capacity if shelves else 0
            for book in books:
                copies_left = book.total_copies
                while copies_left:
                    while shelf_index < len(shelves) and remaining == 0:
                        shelf_index += 1
                        if shelf_index < len(shelves):
                            remaining = shelves[shelf_index].capacity
                    if shelf_index >= len(shelves):
                        return Response({'error': f'Not enough shelf capacity for {book.title} ({copies_left} copies remain).'}, status=400)
                    count = min(copies_left, remaining)
                    placements[shelves[shelf_index].pk][str(book.pk)] = count
                    book_locations[book.pk].append(shelves[shelf_index].name)
                    copies_left -= count
                    remaining -= count
            for shelf in shelves:
                shelf.placements = placements[shelf.pk]
            if shelves:
                Shelf.objects.bulk_update(shelves, ['placements'], batch_size=500)
            for book in books:
                book.shelf_id = None
                book.shelf_location = ', '.join(book_locations[book.pk])
            if books:
                Book.objects.bulk_update(books, ['shelf', 'shelf_location'], batch_size=1000)
            return Response({
                'shelves_arranged': len(shelves),
                'books_arranged': len(books),
                'copies_arranged': sum(book.total_copies for book in books),
            })

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
        if is_library_staff(request.user):
            books = books.prefetch_related('under_desk_copies')
        category = request.query_params.get('category')
        availability = request.query_params.get('availability')
        search = request.query_params.get('search')
        name = request.query_params.get('name')
        shelf = request.query_params.get('shelf')
        ordering = request.query_params.get('ordering', 'title')

        if category:
            books = books.filter(category=category)
        if availability:
            books = books.filter(availability=availability)
        if search:
            books = books.filter( \
                Q(title__icontains=search)\
                | Q(author__icontains=search)\
                | Q(isbn__icontains=search)\
            )
        if name:
            books = books.filter(title__icontains=name)
        if shelf:
            books = books.filter(shelf_id=shelf)

        ordering_fields = [
            field for field in ordering.split(',')
            if field.lstrip('-') in self.allowed_ordering_fields
        ]
        books = books.order_by(*(ordering_fields or ['title']))
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(books, request, view=self)
        return paginator.get_paginated_response([
            self.book_data(book, request) for book in page
        ])

    def post(self, request):
        serializer = BookSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            total_copies = serializer.validated_data.get('total_copies', 1)
            serializer.save(
                available_copies=total_copies,\
                availability=AVAILABLE if total_copies > 0 else UNAVAILABLE,\
            )
        except serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.book_data(serializer.instance, request),status=status.HTTP_201_CREATED)

    def put(self, request):
        book = self.get_book_from_request(request)
        
        if isinstance(book, Response):
            return book

        serializer = BookSerializer(book,data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.book_data(serializer.instance, request))

    def patch(self, request):
        book = self.get_book_from_request(request)
        
        if isinstance(book, Response):
            return book

        serializer = BookSerializer(book,data=request.data,partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except serializers.ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
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

from rest_framework import serializers
from .models import Book

class BookSerializer(serializers.ModelSerializer):
    under_desk_copies = serializers.SerializerMethodField()
    shelf_copies = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'category', 'shelf_location',\
            'total_copies', 'available_copies', 'availability',\
                'borrowing_cost', 'borrowing_period', 'under_desk_copies',\
                'shelf_copies', 'created_at']
        read_only_fields = ['id', 'available_copies', 'availability',\
            'under_desk_copies', 'shelf_copies', 'created_at']

    def get_under_desk_copies(self, book):
        return book.under_desk_copies.count()

    def get_shelf_copies(self, book):
        under_desk = book.under_desk_copies.count()
        return max(book.available_copies - under_desk, 0)


class BookMemberSerializer(BookSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'category',\
            'total_copies', 'availability',\
                'borrowing_cost', 'borrowing_period', 'created_at']
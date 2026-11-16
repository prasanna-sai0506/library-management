from rest_framework import serializers
from .models import Book

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'category', 'shelf_location',\
            'total_copies', 'available_copies', 'availability',\
                'borrowing_cost', 'borrowing_period', 'created_at']
        read_only_fields = ['id', 'available_copies', 'availability', 'created_at']


class BookMemberSerializer(BookSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'category',\
            'total_copies', 'availability',\
                'borrowing_cost', 'borrowing_period', 'created_at']
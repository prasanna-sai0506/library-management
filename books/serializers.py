from rest_framework import serializers
from .models import Book

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'category',\
            'total_copies', 'available_copies', 'availability',\
                'borrowing_cost', 'borrowing_period', 'created_at']
        read_only_fields = ['id', 'available_copies', 'availability', 'created_at']

    def create(self, validated_data):
        total_copies = validated_data.get('total_copies', 1)
        validated_data['available_copies'] = total_copies
        if total_copies > 0:
            validated_data['availability'] = Book.AVAILABLE
        else:
            validated_data['availability'] = Book.UNAVAILABLE
        return super().create(validated_data)
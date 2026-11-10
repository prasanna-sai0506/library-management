# borrowings/serializers.py
from rest_framework import serializers
from .models import Borrowing
from books.serializers import BookSerializer
from users.serializers import UserSerializer

class BorrowingSerializer(serializers.ModelSerializer):
    book_details = BookSerializer(source='book', read_only=True)
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = Borrowing
        fields = ['id','user','user_details','book','book_details','borrowed_at',\
            'due_date','returned_at','credits_spent','borrowing_period','late_fee','status']
        read_only_fields = ['id','user','borrowed_at','due_date','returned_at',\
            'credits_spent','borrowing_period','late_fee','status']
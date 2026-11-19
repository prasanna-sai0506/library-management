from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Borrowing
from books.models import UNAVAILABLE, Book
from users.models import User

class BorrowingCreateSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    borrowing_period = serializers.IntegerField(required=False,min_value=1)
    class Meta:
        model = Borrowing
        fields = ['book', 'borrowing_period']

    def validate(self, attrs):
        user = self.context['request'].user
        book = attrs['book']
        if user.role != user.MEMBER:
            raise serializers.ValidationError(
                {'book': 'Only members can borrow books.'}
            )
        if book.available_copies <= 0 or book.availability == UNAVAILABLE:
            raise serializers.ValidationError(
                {'book': 'No copies available for this book.'}
            )
        if Decimal(str(user.credits)) < Decimal(str(book.borrowing_cost)):
            raise serializers.ValidationError(
                {'book': 'Insufficient credits to borrow this book.'}
            )
        attrs.setdefault('borrowing_period', book.borrowing_period)
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=self.context['request'].user.pk)
            book = Book.objects.select_for_update().get(pk=validated_data['book'].pk)
            borrowing_period = validated_data['borrowing_period']
            borrowing_cost = Decimal(str(book.borrowing_cost))
            if book.available_copies <= 0 or user.credits < borrowing_cost:
                raise serializers.ValidationError({'book': 'The book is no longer available to borrow.'})

            user.credits -= borrowing_cost
            user.save(update_fields=['credits'])
            book.available_copies -= 1
            
            if book.available_copies == 0:
                book.availability = UNAVAILABLE
                
            book.save(update_fields=['available_copies', 'availability'])
            return Borrowing.objects.create(
                user=user, \
                book=book, \
                credits_spent=book.borrowing_cost, \
                borrowing_period=borrowing_period, \
                due_date=timezone.now() + timedelta(days=borrowing_period) \
            )

class BorrowingSerializer(serializers.ModelSerializer):
    book_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Borrowing
        fields = ['id','user','book','book_details','borrowed_at',\
            'due_date','returned_at','credits_spent','borrowing_period','late_fee','status']
        read_only_fields = ['id','user','borrowed_at','due_date','returned_at',\
            'credits_spent','borrowing_period','late_fee','status']

    def get_book_details(self, borrowing):
        return {
            'id': borrowing.book_id,
            'title': borrowing.book.title,
        }
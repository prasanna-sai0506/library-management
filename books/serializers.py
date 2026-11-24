from rest_framework import serializers
from django.db import transaction
from django.db.models import Max, Sum
from .models import Book, Shelf

class BookSerializer(serializers.ModelSerializer):
    under_desk_copies = serializers.SerializerMethodField()
    shelf_copies = serializers.SerializerMethodField()
    shelf_id = serializers.PrimaryKeyRelatedField(
        source='shelf',
        queryset=Shelf.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'category', 'shelf_location', 'shelf_id',\
            'total_copies', 'available_copies', 'availability',\
                'borrowing_cost', 'borrowing_period', 'under_desk_copies',\
                'shelf_copies', 'created_at']
        read_only_fields = ['id', 'available_copies', 'availability',\
            'under_desk_copies', 'shelf_copies', 'created_at']

    def get_under_desk_copies(self, book):
        return self._get_under_desk_count(book)

    def get_shelf_copies(self, book):
        under_desk = self._get_under_desk_count(book)
        return max(book.available_copies - under_desk, 0)

    @staticmethod
    def _get_under_desk_count(book):
        if not hasattr(book, '_under_desk_copy_count'):
            book._under_desk_copy_count = book.under_desk_copies.count()
        return book._under_desk_copy_count

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = getattr(self, 'instance', None)
        shelf = attrs.get('shelf', serializers.empty)
        shelf_location = attrs.get('shelf_location', serializers.empty)

        if shelf is not serializers.empty:
            resolved_shelf = shelf
            if shelf is not None and shelf_location is not serializers.empty:
                if str(shelf_location) != shelf.name and str(shelf_location) != str(shelf.pk):
                    raise serializers.ValidationError({
                        'shelf_location': 'Shelf location conflicts with shelf_id.',
                    })
            if shelf is None and shelf_location is not serializers.empty:
                raise serializers.ValidationError({
                    'shelf_location': 'shelf_location and shelf_id=None conflict.',
                })
        elif shelf_location is not serializers.empty:
            label = str(shelf_location).strip()
            if label:
                resolved_shelf = Shelf.objects.filter(name=label).first()
                if resolved_shelf is None and label.isdecimal():
                    resolved_shelf = Shelf.objects.filter(pk=int(label)).first()
                if resolved_shelf is None:
                    raise serializers.ValidationError({
                        'shelf_location': 'Unknown shelf.',
                    })
                attrs['shelf'] = resolved_shelf
            else:
                attrs['shelf'] = None
        else:
            resolved_shelf = instance.shelf if instance else None

        total_copies = attrs.get('total_copies', instance.total_copies if instance else 1)
        resolved_shelf = attrs.get('shelf', resolved_shelf if 'resolved_shelf' in locals() else
                                    (instance.shelf if instance else None))
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        shelf = validated_data.pop('shelf', serializers.empty)
        if 'total_copies' in validated_data:
            old_total = instance.total_copies
            new_total = validated_data['total_copies']
            difference = new_total - old_total
            borrowed = old_total - instance.available_copies
            if new_total < borrowed:
                raise serializers.ValidationError({
                    'total_copies': 'Cannot reduce copies below the borrowed inventory.',
                })
            instance.available_copies += difference
            if instance.available_copies < 0:
                instance.available_copies = 0
        target_shelf = instance.shelf
        if shelf is not serializers.empty:
            target_shelf = shelf
        if target_shelf is not None:
            new_total = validated_data.get('total_copies', instance.total_copies)
            assigned = target_shelf.books.exclude(pk=instance.pk)\
                .aggregate(total=Sum('total_copies'))['total'] or 0
            if assigned + new_total > target_shelf.capacity:
                raise serializers.ValidationError({
                    'total_copies': 'Shelf capacity exceeded.',
                })

        if shelf is not serializers.empty:
            validated_data['shelf'] = shelf
            if shelf is not None:
                validated_data['shelf_location'] = shelf.name
            else:
                validated_data['shelf_location'] = ''

        return super().update(instance, validated_data)

    @transaction.atomic
    def create(self, validated_data):
        shelf = validated_data.pop('shelf', None)
        if shelf is not None:
            total_copies = validated_data.get('total_copies', 1)
            assigned = shelf.books.aggregate(
                total=Sum('total_copies')
            )['total'] or 0
            if assigned + total_copies > shelf.capacity:
                raise serializers.ValidationError({
                    'total_copies': 'Shelf capacity exceeded.',
                })
            validated_data['shelf'] = shelf
            validated_data['shelf_location'] = shelf.name
        total_copies = validated_data.get('total_copies', 1)
        validated_data.setdefault('available_copies', total_copies)
        return super().create(validated_data)


class ShelfSerializer(serializers.ModelSerializer):
    assigned_copies = serializers.SerializerMethodField()
    remaining_capacity = serializers.SerializerMethodField()

    class Meta:
        model = Shelf
        fields = ['id', 'name', 'column_name', 'shelf_number', 'capacity', 'placements', 'assigned_copies',
                  'remaining_capacity', 'created_at']
        read_only_fields = ['id', 'name', 'column_name', 'shelf_number', 'placements', 'assigned_copies',
                            'remaining_capacity', 'created_at']

    def create(self, validated_data):
        column_name = validated_data['column_name'].strip().upper()
        if not column_name.isalpha():
            raise serializers.ValidationError({'column_name': 'Use letters only for the shelf column.'})
        last_number = Shelf.objects.filter(column_name=column_name).aggregate(
            last=Max('shelf_number')
        )['last']
        validated_data['column_name'] = column_name
        validated_data['shelf_number'] = (last_number or 0) + 1
        validated_data['name'] = f"{column_name}-{validated_data['shelf_number']:02d}"
        return super().create(validated_data)

    def get_assigned_copies(self, shelf):
        placements = shelf.placements or {}
        if placements:
            return sum(int(copies) for copies in placements.values())
        if hasattr(shelf, '_assigned_book_copies'):
            return shelf._assigned_book_copies
        return sum(book.total_copies for book in shelf.books.all())

    def get_remaining_capacity(self, shelf):
        return max(shelf.capacity - self.get_assigned_copies(shelf), 0)

    def validate_capacity(self, value):
        if value < 1:
            raise serializers.ValidationError('Capacity must be at least 1.')
        instance = getattr(self, 'instance', None)
        if instance is not None:
            assigned = self.get_assigned_copies(instance)
            if value < assigned:
                raise serializers.ValidationError(
                    'Capacity cannot be lower than assigned copies.'
                )
        return value


class BookMemberSerializer(BookSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'category',\
            'total_copies', 'availability',\
                'borrowing_cost', 'borrowing_period', 'created_at']

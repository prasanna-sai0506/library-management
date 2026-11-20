import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.exceptions import ValidationError

from books.models import Book, Shelf
from books.serializers import BookSerializer, ShelfSerializer

pytestmark = pytest.mark.django_db


def book(**kwargs):
    return Book.objects.create(title='Test', author='Author', isbn=kwargs.pop('isbn', '123'), category='Test', **kwargs)


def test_assign_move_rename_and_capacity():
    a = Shelf.objects.create(name='A', capacity=10)
    b = Shelf.objects.create(name='B', capacity=2)
    item = book(total_copies=3, available_copies=3)
    serializer = BookSerializer(item, data={'shelf_location': str(a.pk)}, partial=True)
    serializer.is_valid(raise_exception=True)
    item = serializer.save()
    assert item.shelf_id == a.pk
    assert ShelfSerializer(a).data['assigned_copies'] == 3
    serializer = BookSerializer(item, data={'shelf_id': b.pk}, partial=True)
    serializer.is_valid(raise_exception=True)
    with pytest.raises(ValidationError):
        serializer.save()
    item.refresh_from_db()
    assert item.shelf_id == a.pk
    a.name = 'Renamed'
    a.save()
    item.refresh_from_db()
    assert item.shelf_location == 'Renamed'
    serializer = BookSerializer(item, data={'shelf_id': None}, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    assert ShelfSerializer(a).data['assigned_copies'] == 0


def test_batch_overflow_idempotent_and_dry_run():
    book(shelf_location='A', total_copies=50)
    book(shelf_location='A', total_copies=30, isbn='456')
    call_command('sync_shelves', create_missing=True, overflow=True, dry_run=True)
    assert Shelf.objects.count() == 0
    call_command('sync_shelves', create_missing=True, overflow=True)
    assert Shelf.objects.count() == 2
    assert not Book.objects.filter(shelf=None).exists()
    call_command('sync_shelves', create_missing=True, overflow=True)
    assert Shelf.objects.count() == 2
    assert all(ShelfSerializer(s).data['remaining_capacity'] >= 0 for s in Shelf.objects.all())


def test_unknown_name_and_conflicting_id():
    shelf = Shelf.objects.create(name='A', capacity=70)
    item = book()
    assert not BookSerializer(item, data={'shelf_location': 'missing'}, partial=True).is_valid()
    assert not BookSerializer(item, data={'shelf_location': 'A', 'shelf_id': None}, partial=True).is_valid()


def test_batch_failure_rolls_back():
    book(shelf_location='A', total_copies=71)
    with pytest.raises(CommandError):
        call_command('sync_shelves', create_missing=True, overflow=True)
    assert Shelf.objects.count() == 0


def test_copy_update_preserves_borrowed_inventory():
    shelf = Shelf.objects.create(name='A', capacity=70)
    item = book(shelf=shelf, total_copies=5, available_copies=2)
    serializer = BookSerializer(item, data={'total_copies': 7}, partial=True)
    serializer.is_valid(raise_exception=True)
    item = serializer.save()
    assert item.available_copies == 4
    assert ShelfSerializer(shelf).data['assigned_copies'] == 7
    serializer = BookSerializer(item, data={'total_copies': 2}, partial=True)
    serializer.is_valid(raise_exception=True)
    with pytest.raises(ValidationError):
        serializer.save()


def test_shelf_api_and_paginated_contents(api_client, authenticate):
    authenticate(is_staff=True)
    shelf = Shelf.objects.create(name='A', capacity=70)
    item = book(total_copies=2)
    response = api_client.patch(f'/library/books/?id={item.pk}', {'shelf_id': shelf.pk}, format='json')
    assert response.status_code == 200
    response = api_client.get('/library/shelves/')
    assert response.data[0]['assigned_copies'] == 2
    response = api_client.get(f'/library/books/?shelf={shelf.pk}')
    assert response.data['count'] == 1
    response = api_client.delete(f'/library/shelves/?id={shelf.pk}')
    assert response.status_code == 409
    item.delete()
    assert ShelfSerializer(shelf).data['assigned_copies'] == 0

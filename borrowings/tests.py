import pytest
from django.utils import timezone
from datetime import timedelta
from model_bakery import baker

from books.models import AVAILABLE, UNAVAILABLE
from users.models import User
from .models import Borrowing, UnderDeskBook


@pytest.mark.django_db
def test_returned_book_is_added_to_under_desk(api_client, authenticate):
    member = authenticate(role=User.MEMBER)
    librarian = baker.make(User, role=User.LIBRARIAN, is_staff=True)
    book = baker.make(
        'books.Book',
        available_copies=0,
        availability=UNAVAILABLE,
        borrowing_cost='5.00',
    )
    borrowing = baker.make(
        Borrowing,
        user=member,
        book=book,
        due_date=timezone.now() + timedelta(days=7),
        borrowing_period=7,
        credits_spent='5.00',
    )

    api_client.force_authenticate(user=librarian)
    response = api_client.post(f'/borrowings/return/?id={borrowing.id}')

    assert response.status_code == 200
    borrowing.refresh_from_db()
    book.refresh_from_db()
    assert borrowing.status == Borrowing.RETURNED
    assert book.available_copies == 1
    assert book.availability == AVAILABLE
    assert UnderDeskBook.objects.filter(borrowing=borrowing, book=book).exists()


@pytest.mark.django_db
def test_borrow_allocates_under_desk_copy_first(api_client, authenticate):
    member = authenticate(role=User.MEMBER, credits=50)
    book = baker.make(
        'books.Book',
        available_copies=1,
        availability=AVAILABLE,
        borrowing_cost='5.00',
        borrowing_period=7,
    )
    returned_borrowing = baker.make(
        Borrowing,
        user=baker.make(User),
        book=book,
        status=Borrowing.RETURNED,
        due_date=timezone.now(),
        borrowing_period=7,
        credits_spent='5.00',
    )
    under_desk_copy = baker.make(UnderDeskBook, borrowing=returned_borrowing, book=book)

    response = api_client.post('/borrowings/', {
        'book': book.id,
        'borrowing_period': 7,
    }, format='json')

    assert response.status_code == 201
    book.refresh_from_db()
    assert book.available_copies == 0
    assert book.availability == UNAVAILABLE
    assert not UnderDeskBook.objects.filter(id=under_desk_copy.id).exists()


@pytest.mark.django_db
def test_librarian_can_close_under_desk(api_client, authenticate):
    authenticate(role=User.LIBRARIAN, is_staff=True)
    book = baker.make('books.Book')
    borrowing = baker.make(
        Borrowing,
        book=book,
        status=Borrowing.RETURNED,
        due_date=timezone.now(),
        borrowing_period=7,
        credits_spent='5.00',
    )
    baker.make(UnderDeskBook, borrowing=borrowing, book=book)

    response = api_client.post('/borrowings/under-desk/close/')

    assert response.status_code == 200
    assert response.data['moved_count'] == 1
    assert UnderDeskBook.objects.count() == 0
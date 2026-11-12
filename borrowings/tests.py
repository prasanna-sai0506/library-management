import pytest
from model_bakery import baker
from rest_framework import status

from books.models import Book
from users.models import User


@pytest.mark.django_db
def test_admin_cannot_borrow_books(authenticate, api_client):
    authenticate(role=User.ADMIN, credits=50.00)
    book = baker.make(Book, borrowing_cost=10.00, available_copies=3)

    response = api_client.post("/api/borrowings/", {"book": book.id}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["error"] == "Only members can borrow books."


@pytest.mark.django_db
def test_staff_member_cannot_borrow_books(authenticate, api_client):
    authenticate(role=User.MEMBER, is_staff=True, credits=50.00)
    book = baker.make(Book, borrowing_cost=10.00, available_copies=3)

    response = api_client.post("/api/borrowings/", {"book": book.id}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["error"] == "Only members can borrow books."

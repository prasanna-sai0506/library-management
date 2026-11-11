# borrowings/tests.py
import pytest
from rest_framework import status
from model_bakery import baker  
from users.models import User
from books.models import Book
from borrowings.models import Borrowing

@pytest.fixture
def create_borrowing(api_client):
    def do_create_borrowing(payload):
        return api_client.post("/api/borrowings/", payload, format="json")
    return do_create_borrowing

@pytest.mark.django_db
class TestCreateBorrowing:

    def test_if_user_is_anonymous_returns_401(self, create_borrowing):
        # Arrange
        book = baker.make(Book, borrowing_cost=10.00, available_copies=3)

        # Act
        response = create_borrowing({"book": book.id})

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_member_with_sufficient_credits_creates_borrowing_returns_201(self, authenticate, create_borrowing):
        # Arrange
        user = authenticate(role=User.MEMBER, credits=50.00)
        book = baker.make(Book, borrowing_cost=10.00, available_copies=3, total_copies=3)

        # Act
        response = create_borrowing({"book": book.id})

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["id"] > 0
        
        user.refresh_from_db()
        book.refresh_from_db()
        assert user.credits == 40.00
        assert book.available_copies == 2

    def test_if_member_has_insufficient_credits_returns_400(self, authenticate, create_borrowing):
        # Arrange
        authenticate(role=User.MEMBER, credits=5.00)
        book = baker.make(Book, borrowing_cost=10.00, available_copies=3)

        # Act
        response = create_borrowing({"book": book.id})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient credits" in response.data["error"]
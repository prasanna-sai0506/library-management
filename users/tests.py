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
        return api_client.post("/borrowings/", payload, format="json")
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
        assert Borrowing.objects.get(book=book).borrowing_period == book.borrowing_period

    def test_member_can_choose_a_custom_borrowing_period(self, authenticate, create_borrowing):
        authenticate(role=User.MEMBER, credits=50.00)
        book = baker.make(
            Book,
            borrowing_cost=10.00,
            borrowing_period=7,
            available_copies=3,
        )

        response = create_borrowing({
            "book": book.id,
            "borrowing_period": 60,
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert Borrowing.objects.get(book=book).borrowing_period == 60

    def test_borrowing_period_must_be_positive(self, authenticate, create_borrowing):
        authenticate(role=User.MEMBER, credits=50.00)
        book = baker.make(Book, borrowing_cost=10.00, available_copies=3)

        response = create_borrowing({
            "book": book.id,
            "borrowing_period": 0,
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_member_has_insufficient_credits_returns_400(self, authenticate, create_borrowing):
        # Arrange
        authenticate(role=User.MEMBER, credits=5.00)
        book = baker.make(Book, borrowing_cost=10.00, available_copies=3)

        # Act
        response = create_borrowing({"book": book.id})

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient credits" in response.data["error"]

    def test_authenticated_user_can_update_profile(self, authenticate, api_client):
        user = authenticate(role=User.MEMBER)

        response = api_client.patch(
            "/auth/users/profile/",
            {
                "username": "updated-user",
                "email": "updated@example.com",
                "password": "newpassword123",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.username == "updated-user"
        assert user.email == "updated@example.com"
        assert user.check_password("newpassword123")
        assert "password" not in response.data

    def test_profile_reports_total_credits_spent(self, authenticate, api_client, create_borrowing):
        authenticate(role=User.MEMBER, credits=50.00)
        book = baker.make(
            Book,
            borrowing_cost=10.00,
            available_copies=3,
        )
        create_borrowing({"book": book.id})

        response = api_client.get("/auth/users/profile/")

        assert response.status_code == status.HTTP_200_OK
        assert str(response.data["total_credits_spent"]) == "10.00"

    def test_members_do_not_see_available_copies(self, authenticate, api_client):
        authenticate(role=User.MEMBER)
        book = baker.make(Book, available_copies=3)

        response = api_client.get(f"/library/books/?id={book.id}")

        assert response.status_code == status.HTTP_200_OK
        assert "available_copies" not in response.data

    def test_librarians_can_see_available_copies(self, authenticate, api_client):
        authenticate(role=User.LIBRARIAN)
        book = baker.make(Book, available_copies=3)

        response = api_client.get(f"/library/books/?id={book.id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["available_copies"] == 3
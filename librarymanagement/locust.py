import random
import uuid
from locust import HttpUser, between, task
from locust.exception import StopUser


class LibraryUser(HttpUser):
    """Authenticated read-heavy workload for the library API."""

    host = "http://127.0.0.1:8000"
    wait_time = between(1, 3)
    categories = (
        "Computer Science",
        "Data Science",
        "History",
        "Philosophy",
        "Mathematics",
        "Business",
        "Science Fiction",
    )

    def on_start(self):
        self.book_ids = []
        self._create_and_authenticate_member()

    def _create_and_authenticate_member(self):
        username = f"loadtest_{uuid.uuid4().hex[:12]}"
        password = f"LoadTest-{uuid.uuid4().hex}!"

        registration = self.client.post(
            "/auth/users/register/",
            json={
                "username": username,
                "email": f"{username}@example.test",
                "password": password,
            },
            name="/auth/users/register/",
        )
        if registration.status_code != 201:
            if registration.status_code == 0:
                error = getattr(registration, "error", "connection refused")
                raise StopUser(f"Cannot connect to {self.host}: {error}")
            raise StopUser(
                f"Load-test user registration failed: {registration.status_code}"
            )

        login = self.client.post(
            "/auth/users/login/",
            json={"username": username, "password": password},
            name="/auth/users/login/",
        )
        if login.status_code != 200:
            raise StopUser(f"Load-test login failed: {login.status_code}")

        access_token = login.json().get("access")
        if not access_token:
            raise StopUser("Load-test login did not return an access token")

        self.client.headers.update({"Authorization": f"Bearer {access_token}"})

    @staticmethod
    def _books_from_response(response):
        payload = response.json()
        return payload.get("results", []) if isinstance(payload, dict) else payload

    @task(4)
    def browse_books(self):
        category = random.choice(self.categories)
        with self.client.get(
            "/library/books/",
            params={"category": category},
            name="/library/books/?category=",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")
                return

            books = self._books_from_response(response)
            self.book_ids = [
                book["id"] for book in books if isinstance(book, dict) and "id" in book
            ]
            response.success()

    @task(2)
    def view_book_detail(self):
        if not self.book_ids:
            return

        book_id = random.choice(self.book_ids)
        self.client.get(
            f"/library/books/{book_id}/",
            name="/library/books/[id]/",
        )

    @task(1)
    def view_borrowing_history(self):
        self.client.get("/api/borrowings/", name="/api/borrowings/")

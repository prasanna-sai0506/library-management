import pytest
from rest_framework.test import APIClient
from model_bakery import baker
from users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticate(api_client):
    def do_authenticate(role=User.MEMBER, is_staff=False, credits=50.00):
        user = baker.make(User, role=role, is_staff=is_staff, credits=credits)
        api_client.force_authenticate(user=user)
        return user

    return do_authenticate

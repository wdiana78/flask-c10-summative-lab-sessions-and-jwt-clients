import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVER_DIR))

import pytest
from app import app
from models import db


@pytest.fixture
def client(tmp_path):
    database_path = tmp_path / "test_productivity.db"

    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_path}",
        JWT_SECRET_KEY="test-secret-key-for-testing-only",
    )

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()

    with app.test_client() as test_client:
        yield test_client

    with app.app_context():
        db.session.remove()
        db.drop_all()


def register_user(client, username="testuser", password="TestPass123"):
    return client.post(
        "/signup",
        json={
            "username": username,
            "password": password,
            "password_confirmation": password,
        },
    )


def login_user(client, username="testuser", password="TestPass123"):
    response = client.post(
        "/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, (
        f"Login failed: {response.status_code} {response.get_json()}"
    )
    return response.get_json()["token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_home_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json()["message"] == "Productivity API is running"


def test_signup_creates_user(client):
    response = register_user(client)
    assert response.status_code == 201
    data = response.get_json()
    assert data["user"]["username"] == "testuser"
    assert data["token"]


def test_signup_rejects_duplicate_username(client):
    assert register_user(client).status_code == 201
    response = register_user(client)
    assert response.status_code == 409


def test_signup_rejects_mismatched_passwords(client):
    response = client.post(
        "/signup",
        json={
            "username": "testuser",
            "password": "TestPass123",
            "password_confirmation": "DifferentPass123",
        },
    )
    assert response.status_code == 400
    assert "Passwords do not match." in response.get_json()["errors"]


def test_login_returns_token(client):
    register_user(client)
    response = client.post(
        "/login",
        json={"username": "testuser", "password": "TestPass123"},
    )
    assert response.status_code == 200
    assert response.get_json()["token"]


def test_login_rejects_wrong_password(client):
    register_user(client)
    response = client.post(
        "/login",
        json={"username": "testuser", "password": "WrongPass123"},
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/me")
    assert response.status_code == 401


def test_me_returns_authenticated_user(client):
    register_user(client)
    token = login_user(client)
    response = client.get("/me", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.get_json()["username"] == "testuser"


def test_journal_crud(client):
    register_user(client)
    headers = auth_headers(login_user(client))

    created = client.post(
        "/journal_entries",
        json={
            "title": "Test journal entry",
            "content": "Testing the journal API.",
            "mood": "Focused",
        },
        headers=headers,
    )
    assert created.status_code == 201
    entry_id = created.get_json()["id"]

    listed = client.get(
        "/journal_entries?page=1&per_page=10",
        headers=headers,
    )
    assert listed.status_code == 200
    assert listed.get_json()["pagination"]["total_entries"] == 1

    retrieved = client.get(
        f"/journal_entries/{entry_id}",
        headers=headers,
    )
    assert retrieved.status_code == 200
    assert retrieved.get_json()["title"] == "Test journal entry"

    updated = client.patch(
        f"/journal_entries/{entry_id}",
        json={"title": "Updated title"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.get_json()["title"] == "Updated title"

    deleted = client.delete(
        f"/journal_entries/{entry_id}",
        headers=headers,
    )
    assert deleted.status_code == 200

    missing = client.get(
        f"/journal_entries/{entry_id}",
        headers=headers,
    )
    assert missing.status_code == 404


def test_user_cannot_access_another_users_entry(client):
    register_user(client, "owner", "OwnerPass123")
    owner_token = login_user(client, "owner", "OwnerPass123")

    created = client.post(
        "/journal_entries",
        json={
            "title": "Private entry",
            "content": "Only the owner should see this.",
            "mood": "Calm",
        },
        headers=auth_headers(owner_token),
    )
    assert created.status_code == 201
    entry_id = created.get_json()["id"]

    register_user(client, "otheruser", "OtherPass123")
    other_token = login_user(client, "otheruser", "OtherPass123")

    response = client.get(
        f"/journal_entries/{entry_id}",
        headers=auth_headers(other_token),
    )
    assert response.status_code == 404


def test_journal_endpoints_require_authentication(client):
    response = client.get("/journal_entries")
    assert response.status_code == 401


def test_pagination_rejects_invalid_page(client):
    register_user(client)
    headers = auth_headers(login_user(client))

    response = client.get(
        "/journal_entries?page=0",
        headers=headers,
    )
    assert response.status_code == 400

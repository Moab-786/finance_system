from app import models
from tests.conftest import create_user


def test_register_success(client):
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
        "role": "viewer",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert data["role"] == payload["role"]


def test_register_duplicate_email(client, db_session):
    create_user(
        db_session,
        username="existing",
        email="existing@example.com",
        role=models.UserRole.viewer,
    )

    payload = {
        "username": "another",
        "email": "existing@example.com",
        "password": "password123",
        "role": "viewer",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_success(client, db_session):
    create_user(
        db_session,
        username="loginuser",
        email="login@example.com",
        role=models.UserRole.viewer,
    )

    response = client.post(
        "/auth/login",
        data={"username": "loginuser", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client, db_session):
    create_user(
        db_session,
        username="badlogin",
        email="badlogin@example.com",
        role=models.UserRole.viewer,
    )

    response = client.post(
        "/auth/login",
        data={"username": "badlogin", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_refresh_token_and_logout(client, db_session):
    user = create_user(
        db_session,
        username="refreshuser",
        email="refresh@example.com",
        role=models.UserRole.viewer,
    )

    login_response = client.post(
        "/auth/login",
        data={"username": "refreshuser", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    tokens = login_response.json()

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()

    logout_response = client.post(
        "/auth/logout",
        json={"token": tokens["access_token"]},
    )
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Logged out successfully"

    protected_response = client.get(
        "/transactions/",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert protected_response.status_code == 401

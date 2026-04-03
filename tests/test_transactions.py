from datetime import datetime, timedelta, timezone

from app import models
from tests.conftest import create_user, get_auth_headers


def test_admin_can_create_transaction(client, db_session):
    admin = create_user(db_session, "admin1", "admin1@example.com", models.UserRole.admin)
    headers = get_auth_headers(admin)

    payload = {
        "amount": 1200.5,
        "type": "income",
        "category": "salary",
        "notes": "monthly payroll",
    }
    response = client.post("/transactions/", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == payload["amount"]
    assert data["category"] == payload["category"]


def test_viewer_cannot_create_transaction(client, db_session):
    viewer = create_user(db_session, "viewer1", "viewer1@example.com", models.UserRole.viewer)
    headers = get_auth_headers(viewer)

    payload = {
        "amount": 100,
        "type": "expense",
        "category": "food",
    }
    response = client.post("/transactions/", json=payload, headers=headers)

    assert response.status_code == 403


def test_user_only_sees_own_transactions(client, db_session):
    admin = create_user(db_session, "admin2", "admin2@example.com", models.UserRole.admin)
    user_a = create_user(db_session, "usera", "usera@example.com", models.UserRole.viewer)
    user_b = create_user(db_session, "userb", "userb@example.com", models.UserRole.viewer)

    db_session.add(
            models.Transaction(
            amount=50,
            type=models.TransactionType.expense,
            category="food",
                date=datetime.now(timezone.utc),
            user_id=user_a.id,
        )
    )
    db_session.add(
            models.Transaction(
            amount=100,
            type=models.TransactionType.income,
            category="salary",
                date=datetime.now(timezone.utc),
            user_id=user_b.id,
        )
    )
    db_session.commit()

    user_a_response = client.get("/transactions/", headers=get_auth_headers(user_a))
    admin_response = client.get("/transactions/", headers=get_auth_headers(admin))

    assert user_a_response.status_code == 200
    assert admin_response.status_code == 200

    user_a_items = user_a_response.json()["items"]
    admin_items = admin_response.json()["items"]

    assert len(user_a_items) == 1
    assert user_a_items[0]["user_id"] == user_a.id
    assert len(admin_items) == 2


def test_cannot_read_other_users_transaction(client, db_session):
    user_a = create_user(db_session, "reader_a", "reader_a@example.com", models.UserRole.viewer)
    user_b = create_user(db_session, "reader_b", "reader_b@example.com", models.UserRole.viewer)

    record = models.Transaction(
        amount=220,
        type=models.TransactionType.expense,
        category="travel",
        date=datetime.now(timezone.utc),
        user_id=user_b.id,
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    response = client.get(f"/transactions/{record.id}", headers=get_auth_headers(user_a))

    assert response.status_code == 403


def test_transaction_filters_and_pagination(client, db_session):
    user = create_user(db_session, "filteruser", "filter@example.com", models.UserRole.viewer)

    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            models.Transaction(
                amount=100,
                type=models.TransactionType.expense,
                category="food",
                notes="lunch",
                date=now - timedelta(days=1),
                user_id=user.id,
            ),
            models.Transaction(
                amount=200,
                type=models.TransactionType.expense,
                category="travel",
                notes="flight",
                date=now - timedelta(days=2),
                user_id=user.id,
            ),
            models.Transaction(
                amount=300,
                type=models.TransactionType.income,
                category="salary",
                notes="bonus",
                date=now - timedelta(days=3),
                user_id=user.id,
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        "/transactions/?type=expense&search=fl&skip=0&limit=5&sort_by=amount&sort_order=asc",
        headers=get_auth_headers(user),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["category"] == "travel"


def test_reject_future_date(client, db_session):
    admin = create_user(db_session, "admin3", "admin3@example.com", models.UserRole.admin)

    future_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    payload = {
        "amount": 120,
        "type": "income",
        "category": "salary",
        "date": future_date,
    }

    response = client.post("/transactions/", json=payload, headers=get_auth_headers(admin))

    assert response.status_code == 422

from datetime import datetime, timezone

from app import models
from tests.conftest import create_user, get_auth_headers


def test_analytics_summary_for_analyst(client, db_session):
    analyst = create_user(db_session, "analyst1", "analyst1@example.com", models.UserRole.analyst)
    owner = create_user(db_session, "owner1", "owner1@example.com", models.UserRole.viewer)

    db_session.add_all(
        [
            models.Transaction(
                amount=1000,
                type=models.TransactionType.income,
                category="salary",
                date=datetime.now(timezone.utc),
                user_id=owner.id,
            ),
            models.Transaction(
                amount=200,
                type=models.TransactionType.expense,
                category="food",
                date=datetime.now(timezone.utc),
                user_id=owner.id,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/analytics/summary", headers=get_auth_headers(analyst))

    assert response.status_code == 200
    data = response.json()
    assert data["total_income"] == 1000
    assert data["total_expenses"] == 200
    assert data["balance"] == 800


def test_analytics_forbidden_for_viewer(client, db_session):
    viewer = create_user(db_session, "viewer2", "viewer2@example.com", models.UserRole.viewer)

    response = client.get("/analytics/summary", headers=get_auth_headers(viewer))

    assert response.status_code == 403

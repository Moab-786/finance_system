from io import BytesIO

from app import models
from tests.conftest import create_user, get_auth_headers


def test_export_transactions_as_csv(client, db_session):
    admin = create_user(db_session, "exportadmin", "exportadmin@example.com", models.UserRole.admin)
    db_session.add(
        models.Transaction(
            amount=450,
            type=models.TransactionType.income,
            category="salary",
            notes="monthly salary",
            user_id=admin.id,
        )
    )
    db_session.commit()

    response = client.get("/transactions/export", headers=get_auth_headers(admin))

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "transactions.csv" in response.headers["content-disposition"]
    assert "salary" in response.text


def test_import_transactions_from_csv(client, db_session):
    admin = create_user(db_session, "importadmin", "importadmin@example.com", models.UserRole.admin)
    csv_payload = (
        "amount,type,category,date,notes\n"
        "100,income,salary,2026-01-01T10:00:00,bonus\n"
        "25,expense,food,2026-01-02T12:00:00,lunch\n"
    )

    response = client.post(
        "/transactions/import",
        files={"file": ("transactions.csv", csv_payload, "text/csv")},
        headers=get_auth_headers(admin),
    )

    assert response.status_code == 200
    assert response.json()["count"] == 2

    list_response = client.get("/transactions/", headers=get_auth_headers(admin))
    assert list_response.json()["total"] == 2
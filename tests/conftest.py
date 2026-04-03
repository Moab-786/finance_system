from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.auth import hash_password, create_access_token
from app import models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_finance.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def create_user(db, username: str, email: str, role: models.UserRole, password: str = "password123"):
    user = models.User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_headers(user: models.User):
    token = create_access_token({"sub": user.username, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


def clear_tables(db):
    db.query(models.Transaction).delete()
    db.query(models.User).delete()
    db.commit()


import pytest


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def db_session():
    db = TestingSessionLocal()
    clear_tables(db)
    try:
        yield db
    finally:
        clear_tables(db)
        db.close()

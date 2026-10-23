import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.user import User
from app.security import hash_password, create_access_token
from typing import Literal
from datetime import datetime, timedelta, timezone
import jwt

from app.security import SECRET_KEY, ALGORITHM

from app.main import app
from app.database import Base, get_db


TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()



@pytest.fixture(autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    # Create a test user.
    db = TestingSessionLocal()
    try:
        user = User(
            email="test@example.com",
            hashed_password=hash_password("TestPassword123!")
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Generate a real JWT for the test user.
        token = create_access_token(user.id)
    finally:
        db.close()

    # Authenticate requests made by this test.
    client.headers.update({
        "Authorization": f"Bearer {token}"
    })

    yield

    client.headers.pop("Authorization", None)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)



client = TestClient(app)


def test_read_nonexistent_project():
    response = client.get("/projects/999999")

    assert response.status_code == 404
    assert response.json() == {
    "detail": "Project 999999 not found"
}

def test_create_project():
    response = client.post(
        "/projects/",
        json={
            "name": "Test Project",
            "description": "Created during automated testing"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Project"
    assert data["description"] == "Created during automated testing"
    assert "id" in data
    assert "created_at" in data


def test_update_project():
    create_response = client.post(
        "/projects/",
        json={
            "name": "Original Project",
            "description": "Original description"
        }
    )

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/projects/{project_id}",
        json={"name": "Updated Project"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Project"
    assert data["description"] == "Original description"


def test_delete_project():
    create_response = client.post(
        "/projects/",
        json={
            "name": "Project to Delete",
            "description": "Temporary project"
        }
    )

    project_id = create_response.json()["id"]

    response = client.delete(f"/projects/{project_id}")

    assert response.status_code == 204

    get_response = client.get(f"/projects/{project_id}")
    assert get_response.status_code == 404


def test_create_project_with_invalid_name():
    response = client.post(
        "/projects/",
        json={
            "name": "AB",
            "description": "Valid description"
        }
    )

    assert response.status_code == 422

def test_update_project_with_null_name():
    create_response = client.post(
        "/projects/",
        json={
            "name": "Valid Project",
            "description": "Valid description"
        }
    )

    project_id = create_response.json()["id"]

    response = client.patch(
        f"/projects/{project_id}",
        json={"name": None}
    )

    assert response.status_code == 422

    get_response = client.get(f"/projects/{project_id}")

    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Valid Project"


def test_list_projects():
    client.post(
        "/projects/",
        json={
            "name": "Alpha Project",
            "description": "First project"
        }
    )

    client.post(
        "/projects/",
        json={
            "name": "Beta Project",
            "description": "Second project"
        }
    )

    response = client.get("/projects/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["name"] == "Alpha Project"
    assert data[1]["name"] == "Beta Project"


def test_list_projects_pagination():
    for name in ["Alpha", "Beta", "Gamma"]:
        client.post(
            "/projects/",
            json={
                "name": name,
                "description": f"{name} description"
            }
        )

    response = client.get("/projects/?skip=1&limit=1")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Beta"


def test_list_projects_search():
    client.post(
        "/projects/",
        json={
            "name": "FastAPI Service",
            "description": "Backend API"
        }
    )

    client.post(
        "/projects/",
        json={
            "name": "Analytics Dashboard",
            "description": "Data visualization"
        }
    )

    response = client.get("/projects/?search=FastAPI")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "FastAPI Service"


def test_list_projects_sort_by_name():
    for name in ["Gamma", "Alpha", "Beta"]:
        client.post(
            "/projects/",
            json={
                "name": name,
                "description": f"{name} description"
            }
        )

    response = client.get("/projects/?sort_by=name")

    assert response.status_code == 200

    names = [project["name"] for project in response.json()]

    assert names == ["Alpha", "Beta", "Gamma"]


def test_list_projects_invalid_sort_by():
    response = client.get("/projects/?sort_by=description")

    assert response.status_code == 422


def test_projects_require_authentication():
    response = client.get(
        "/projects/",
        headers={"Authorization": ""}
    )

    assert response.status_code == 401


def test_user_cannot_access_another_users_project():
    # User A is the authenticated user from the fixture.
    create_response = client.post(
        "/projects/",
        json={
            "name": "User A Project",
            "description": "Private project"
        }
    )

    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Create User B in the same test database.
    db = TestingSessionLocal()
    try:
        user_b = User(
            email="userb@example.com",
            hashed_password=hash_password("UserBPassword123!")
        )
        db.add(user_b)
        db.commit()
        db.refresh(user_b)

        user_b_token = create_access_token(user_b.id)
    finally:
        db.close()

    # Switch authentication from User A to User B.
    client.headers.update({
        "Authorization": f"Bearer {user_b_token}"
    })

    # User B must not be able to access User A's project.
    response = client.get(f"/projects/{project_id}")
    assert response.status_code == 404

    response = client.patch(
        f"/projects/{project_id}",
        json={"name": "Hijacked Project"}
    )
    assert response.status_code == 404

    response = client.delete(f"/projects/{project_id}")
    assert response.status_code == 404


def test_users_only_see_their_own_projects():
    # User A creates a project.
    response = client.post(
        "/projects/",
        json={
            "name": "User A Project",
            "description": "Owned by User A"
        }
    )
    assert response.status_code == 201

    # Create User B and generate a token.
    db = TestingSessionLocal()
    try:
        user_b = User(
            email="userb@example.com",
            hashed_password=hash_password("UserBPassword123!")
        )
        db.add(user_b)
        db.commit()
        db.refresh(user_b)

        token_b = create_access_token(user_b.id)
    finally:
        db.close()

    # Switch to User B.
    client.headers.update({
        "Authorization": f"Bearer {token_b}"
    })

    # User B should not see User A's project.
    response = client.get("/projects/")

    assert response.status_code == 200
    assert response.json() == []


def test_registration_rejects_duplicate_email():
    from app.routers.users import register_user
    from app.schemas.user import UserCreate

    db = TestingSessionLocal()
    try:
        try:
            register_user(
                UserCreate(
                    email="test@example.com",
                    password="AnotherPassword123!"
                ),
                db
            )
            assert False, "Expected duplicate registration to fail"
        except Exception as exc:
            from fastapi import HTTPException

            assert isinstance(exc, HTTPException)
            assert exc.status_code == 409
    finally:
        db.close()


def test_registration_rejects_invalid_email():
    response = client.post(
        "/users/register",
        json={
            "email": "not-an-email",
            "password": "StrongPassword123!"
        }
    )

    assert response.status_code == 422


def test_projects_reject_invalid_token():
    response = client.get(
        "/projects/",
        headers={"Authorization": "Bearer invalid.token.value"}
    )

    assert response.status_code == 401


def test_projects_reject_expired_token():
    expired_token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1)
        },
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    response = client.get(
        "/projects/",
        headers={"Authorization": f"Bearer {expired_token}"}
    )

    assert response.status_code == 401

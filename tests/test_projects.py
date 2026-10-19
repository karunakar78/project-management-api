import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Literal

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

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_read_nonexistent_project():
    response = client.get("/projects/999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Project not found"
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
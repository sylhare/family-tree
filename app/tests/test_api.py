import pytest
from fastapi.testclient import TestClient

from src.main import app


class FakeSession:  # Simple stub that records Cypher statements
    def __init__(self):
        self.queries = []

    def run(self, query, **kwargs):
        # Store the query for potential assertions
        self.queries.append((query, kwargs))

    # Support "with driver.session() as session:" syntax
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class FakeDriver:
    def __init__(self):
        self.session_obj = FakeSession()

    def session(self):
        return self.session_obj

    def close(self):
        pass


@pytest.fixture()
def client(monkeypatch):
    """FastAPI TestClient with Neo4j driver mocked out."""
    fake_driver = FakeDriver()

    # Patch the get_driver function at the routes module level where it's imported
    monkeypatch.setattr("src.routes.get_driver", lambda: fake_driver)

    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_tree_success(client):
    payload = {
        "persons": [
            {"id": "1", "name": "John", "birth": "1970-01-01"},
            {"id": "2", "name": "Jane", "birth": "1972-02-14"},
        ],
        "relationships": [
            {"start_id": "1", "end_id": "2", "type": "MARRIED"}
        ],
    }
    resp = client.post("/tree", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "success"}


def test_create_tree_invalid_relationship(client):
    payload = {
        "persons": [
            {"id": "1", "name": "John"},
            {"id": "2", "name": "Jane"},
        ],
        "relationships": [
            {"start_id": "1", "end_id": "2", "type": "MARRIED TO"}  # invalid (space)
        ],
    }
    resp = client.post("/tree", json=payload)

    assert resp.status_code == 400
    assert "Invalid relationship type" in resp.json()["detail"] 
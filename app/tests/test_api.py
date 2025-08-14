import pytest
from fastapi.testclient import TestClient

from src.main import app


class FakeResult:
    def __init__(self, records):
        self._records = records

    def __iter__(self):
        return iter(self._records)

    def __next__(self):
        return next(self._records)


class FakeRecord(dict):
    """Simple mapping-like record to access by key."""
    def __getattr__(self, item):
        return self[item]


class FakeSession:  # Simple stub that records Cypher statements
    def __init__(self):
        self.queries = []
        self._persons = []
        self._rels = []

    def run(self, query, **kwargs):
        # Store the query for potential assertions
        self.queries.append((query, kwargs))
        q = query.strip().lower()
        if q.startswith("match (p:person)"):
            # Return persons
            return FakeResult([FakeRecord(p) for p in self._persons])
        if q.startswith("match (a:person)-[r]->(b:person)"):
            # Return relationships
            return FakeResult([FakeRecord(r) for r in self._rels])
        return FakeResult([])

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
        # expose driver for test to mutate fixture data
        c.fake_driver = fake_driver
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


def test_get_tree_empty(client):
    # By default, fake driver has no data
    resp = client.get("/tree")
    assert resp.status_code == 200
    assert resp.json() == {"persons": [], "relationships": []}


def test_get_tree_with_data(client):
    # Seed fake data via the fake driver's session
    session = client.fake_driver.session_obj
    session._persons = [
        {"id": "1", "name": "John", "birth": "1970-01-01"},
        {"id": "2", "name": "Jane", "birth": None},
    ]
    session._rels = [
        {"start_id": "1", "end_id": "2", "type": "MARRIED"},
    ]

    resp = client.get("/tree")
    assert resp.status_code == 200
    data = resp.json()
    assert data["persons"] == session._persons
    assert data["relationships"] == session._rels 
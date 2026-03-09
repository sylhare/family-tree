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


def test_import_gedcomx_success(client):
    """Test successful GEDCOM X import with persons and relationships."""
    payload = {
        "persons": [
            {
                "id": "I1",
                "names": [
                    {
                        "nameForms": [
                            {"fullText": "John Doe"}
                        ]
                    }
                ],
                "facts": [
                    {
                        "type": "http://gedcomx.org/Birth",
                        "date": {"original": "1970-01-01"}
                    }
                ]
            },
            {
                "id": "I2",
                "display": {"name": "Jane Smith"},
                "facts": []
            }
        ],
        "relationships": [
            {
                "type": "http://gedcomx.org/Couple",
                "person1": {"resource": "#I1"},
                "person2": {"resource": "#I2"}
            }
        ]
    }
    
    resp = client.post("/import/gedcomx", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "success"}
    
    # Verify queries were executed
    session = client.fake_driver.session_obj
    assert len(session.queries) >= 3  # 2 person creates + 1 relationship create


def test_import_gedcomx_with_parent_child_relationship(client):
    """Test GEDCOM X import with parent-child relationship."""
    payload = {
        "persons": [
            {"id": "I1", "display": {"name": "Father"}},
            {"id": "I2", "display": {"name": "Child"}}
        ],
        "relationships": [
            {
                "type": "http://gedcomx.org/ParentChild",
                "person1": {"resource": "#I1"},
                "person2": {"resource": "#I2"}
            }
        ]
    }
    
    resp = client.post("/import/gedcomx", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "success"}


def test_import_gedcomx_empty_payload(client):
    """Test GEDCOM X import with empty payload."""
    payload = {}
    
    resp = client.post("/import/gedcomx", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "success"}


def test_import_gedcomx_persons_only(client):
    """Test GEDCOM X import with only persons, no relationships."""
    payload = {
        "persons": [
            {"id": "I1", "display": {"name": "Solo Person"}}
        ]
    }
    
    resp = client.post("/import/gedcomx", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "success"}


def test_import_gedcomx_invalid_json(client):
    """Test GEDCOM X import with invalid JSON structure."""
    # Send a string instead of dict
    resp = client.post("/import/gedcomx", json="invalid")
    assert resp.status_code == 422  # FastAPI returns 422 for validation errors
    assert "Invalid JSON payload" not in resp.json().get("detail", "")  # FastAPI's own validation error


def test_import_gedcomx_person_without_id(client):
    """Test GEDCOM X import ignores persons without ID."""
    payload = {
        "persons": [
            {"display": {"name": "No ID Person"}},  # Missing id field
            {"id": "I1", "display": {"name": "Valid Person"}}
        ]
    }
    
    resp = client.post("/import/gedcomx", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "success"}
    
    # Should only have 1 person query (for the valid person)
    session = client.fake_driver.session_obj
    person_queries = [q for q in session.queries if "MERGE (n:Person" in q[0]]
    assert len(person_queries) == 1


def test_import_gedcomx_relationship_without_persons(client):
    """Test GEDCOM X import attempts to create relationships even with missing person references."""
    payload = {
        "persons": [
            {"id": "I1", "display": {"name": "Person One"}}
        ],
        "relationships": [
            {
                "type": "http://gedcomx.org/Couple",
                "person1": {"resource": "#I1"},
                "person2": {"resource": "#MISSING"}  # Non-existent person
            },
            {
                "type": "http://gedcomx.org/Couple",
                # Missing person1 and person2 - should be skipped
            }
        ]
    }
    
    resp = client.post("/import/gedcomx", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "success"}
    
    # Should have 1 person query and 1 relationship query (first relationship)
    # The second relationship is skipped because person1/person2 are empty
    session = client.fake_driver.session_obj
    person_queries = [q for q in session.queries if "MERGE (n:Person" in q[0]]
    relationship_queries = [q for q in session.queries if "MERGE (a)-[rel:" in q[0]]
    assert len(person_queries) == 1
    assert len(relationship_queries) == 1  # One relationship query attempted


def test_import_gedcomx_unknown_relationship_type(client):
    """Test GEDCOM X import handles unknown relationship types."""
    payload = {
        "persons": [
            {"id": "I1", "display": {"name": "Person One"}},
            {"id": "I2", "display": {"name": "Person Two"}}
        ],
        "relationships": [
            {
                "type": "http://example.com/CustomRelation",
                "person1": {"resource": "#I1"},
                "person2": {"resource": "#I2"}
            }
        ]
    }
    
    resp = client.post("/import/gedcomx", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "success"}
    
    # Should create relationship with fallback type
    session = client.fake_driver.session_obj
    relationship_queries = [q for q in session.queries if "MERGE (a)-[rel:" in q[0]]
    assert len(relationship_queries) == 1 
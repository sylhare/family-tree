from fastapi import APIRouter, HTTPException, Body

from .models import GenealogicalTree
from .db import get_driver, close_driver

router = APIRouter()


@router.get("/health", tags=["Utility"])
async def health_check():
    """Simple health-check endpoint."""
    return {"status": "ok"}


@router.post("/tree", tags=["Genealogy"], summary="Ingest a genealogical tree")
async def create_tree(tree: GenealogicalTree):
    """Persist the provided genealogical tree into Neo4j.

    Accepts a JSON payload with `persons` and `relationships` arrays.
    """
    driver = get_driver()
    try:
        with driver.session() as session:
            # Create / update persons
            for person in tree.persons:
                session.run(
                    """
                    MERGE (p:Person {id: $id})
                    SET   p.name = $name,
                          p.birth = $birth
                    """,
                    id=person.id,
                    name=person.name,
                    birth=person.birth,
                )

            # Create / update relationships
            for rel in tree.relationships:
                rel_type = rel.type.upper()
                if not rel_type.isidentifier():
                    raise HTTPException(status_code=400, detail=f"Invalid relationship type: {rel.type}")

                cypher = (
                    f"MATCH (a:Person {{id: $start_id}}), (b:Person {{id: $end_id}}) "
                    f"MERGE (a)-[r:{rel_type}]->(b)"
                )
                session.run(cypher, start_id=rel.start_id, end_id=rel.end_id)

        return {"status": "success"}

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    finally:
        close_driver(driver)


@router.get("/tree", tags=["Genealogy"], summary="Retrieve the current genealogical tree")
async def get_tree():
    """Fetch all persons and relationships from Neo4j and return as a GenealogicalTree."""
    driver = get_driver()
    try:
        with driver.session() as session:
            # Fetch persons
            persons_result = session.run(
                """
                MATCH (p:Person)
                RETURN p.id AS id, p.name AS name, p.birth AS birth
                ORDER BY name
                """
            )
            persons = [
                {"id": record["id"], "name": record["name"], "birth": record["birth"]}
                for record in persons_result
            ]

            # Fetch relationships of interest between persons
            relationships_result = session.run(
                """
                MATCH (a:Person)-[r]->(b:Person)
                RETURN a.id AS start_id, b.id AS end_id, type(r) AS type
                """
            )
            relationships = [
                {
                    "start_id": record["start_id"],
                    "end_id": record["end_id"],
                    "type": record["type"],
                }
                for record in relationships_result
            ]

        return {"persons": persons, "relationships": relationships}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    finally:
        close_driver(driver)


def _extract_name(person: dict) -> str:
    names = person.get("names") or []
    if names:
        forms = names[0].get("nameForms") or []
        if forms:
            full = forms[0].get("fullText")
            if full:
                return full
    return person.get("display", {}).get("name") or person.get("id") or "Unknown"


def _extract_birth(person: dict) -> str | None:
    facts = person.get("facts") or []
    for fact in facts:
        if str(fact.get("type", "")).lower().endswith("/birth"):
            date = (fact.get("date") or {}).get("original")
            return date
    return None


def _gx_ref_to_id(ref: str) -> str:
    # references are often like "#I1"; strip leading '#'
    return ref[1:] if ref and ref.startswith('#') else ref


@router.post("/import/gedcomx", tags=["Genealogy"], summary="Import a GEDCOM X JSON payload")
async def import_gedcomx(payload: dict = Body(...)):
    """Import GEDCOM X JSON and store persons/relationships.

    Expects a JSON body with `persons` and `relationships` arrays as per GEDCOM X.
    Stores relationships with types COUPLE or PARENT_CHILD, preserving original gx_type.
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    persons = payload.get("persons") or []
    relationships = payload.get("relationships") or []

    driver = get_driver()
    try:
        with driver.session() as session:
            # Persons
            for p in persons:
                pid = p.get("id")
                if not pid:
                    continue
                name = _extract_name(p)
                birth = _extract_birth(p)
                session.run(
                    """
                    MERGE (n:Person {id: $id})
                    SET n.name = $name,
                        n.birth = $birth,
                        n.gx_id = $gx_id
                    """,
                    id=pid,
                    name=name,
                    birth=birth,
                    gx_id=pid,
                )

            # Relationships
            for r in relationships:
                gx_type = r.get("type", "")
                t = gx_type.split('/')[-1].upper() if gx_type else ""
                if t == "COUPLE":
                    rel_type = "COUPLE"
                elif t == "PARENTCHILD" or t == "PARENT_CHILD":
                    rel_type = "PARENT_CHILD"
                else:
                    # Fallback to identifier-safe mapping
                    rel_type = (t or "RELATED").upper()
                    rel_type = ''.join(ch if ch.isalnum() else '_' for ch in rel_type)
                    if not rel_type.isidentifier():
                        rel_type = "RELATED"

                src = _gx_ref_to_id(((r.get("person1") or {}).get("resource")) or "")
                dst = _gx_ref_to_id(((r.get("person2") or {}).get("resource")) or "")
                if not src or not dst:
                    continue

                session.run(
                    f"""
                    MATCH (a:Person {{id: $a}}), (b:Person {{id: $b}})
                    MERGE (a)-[rel:{rel_type}]->(b)
                    SET rel.gx_type = $gx
                    """,
                    a=src,
                    b=dst,
                    gx=gx_type,
                )

        return {"status": "success"}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    finally:
        close_driver(driver) 
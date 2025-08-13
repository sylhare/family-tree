from fastapi import APIRouter, HTTPException

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
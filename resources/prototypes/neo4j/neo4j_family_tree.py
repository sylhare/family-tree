"""
Minimal Neo4j prototype: create two Person nodes + a PARENT_OF relationship,
then query and print children.

Prerequisites:
  pip install neo4j   (or: uv add neo4j)
  Neo4j running — see README.md

Environment variables (optional, defaults shown):
  NEO4J_URI      bolt://localhost:7687
  NEO4J_USER     neo4j
  NEO4J_PASSWORD password
"""

import os
from neo4j import GraphDatabase

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def create_family(tx):
    tx.run(
        "MERGE (p:Person {name: $parent}) "
        "MERGE (c:Person {name: $child}) "
        "MERGE (p)-[:PARENT_OF]->(c)",
        parent="Alice",
        child="Bob",
    )


def get_children(tx, parent_name):
    result = tx.run(
        "MATCH (p:Person {name: $name})-[:PARENT_OF]->(c:Person) RETURN c.name AS name",
        name=parent_name,
    )
    return [record["name"] for record in result]


def main():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    with driver.session() as session:
        session.execute_write(create_family)
        children = session.execute_read(get_children, "Alice")
        print(f"Children of Alice: {children}")
    driver.close()


if __name__ == "__main__":
    main()

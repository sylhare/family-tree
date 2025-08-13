import os
from neo4j import GraphDatabase


def get_driver():
    """Create a Neo4j driver using environment variables or sensible defaults."""
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(user, password))


def close_driver(driver):
    if driver:
        driver.close() 
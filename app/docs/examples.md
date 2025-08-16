# Genealogical Tree API - Examples & Usage

This document provides practical examples of how to use the Genealogical Tree API and interact with the stored data in Neo4j.

## Prerequisites

Make sure the application is running with Docker Compose:

```bash
cd app
docker compose up --build -d
```

## API Usage Examples

### 1. Health Check

Test if the API is running:

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{"status": "ok"}
```

### 2. Creating a Family Tree

#### Basic Family Example

```bash
curl -X POST http://localhost:8000/tree \
     -H "Content-Type: application/json" \
     -d '{
           "persons": [
             {"id": "1", "name": "John", "birth": "1970-01-01"},
             {"id": "2", "name": "Jane", "birth": "1972-02-14"},
             {"id": "3", "name": "Alice", "birth": "2000-05-30"}
           ],
           "relationships": [
             {"start_id": "1", "end_id": "2", "type": "MARRIED"},
             {"start_id": "1", "end_id": "3", "type": "PARENT_OF"},
             {"start_id": "2", "end_id": "3", "type": "PARENT_OF"}
           ]
         }'
```

**Expected response:**
```json
{"status": "success"}
```

#### Extended Family Example

```bash
curl -X POST http://localhost:8000/tree \
     -H "Content-Type: application/json" \
     -d '{
           "persons": [
             {"id": "4", "name": "Robert", "birth": "1945-03-15"},
             {"id": "5", "name": "Mary", "birth": "1948-07-22"},
             {"id": "6", "name": "Michael", "birth": "1998-12-10"},
             {"id": "7", "name": "Sarah", "birth": "2002-08-05"}
           ],
           "relationships": [
             {"start_id": "4", "end_id": "5", "type": "MARRIED"},
             {"start_id": "4", "end_id": "1", "type": "PARENT_OF"},
             {"start_id": "5", "end_id": "1", "type": "PARENT_OF"},
             {"start_id": "3", "end_id": "6", "type": "PARENT_OF"},
             {"start_id": "3", "end_id": "7", "type": "PARENT_OF"}
           ]
         }'
```

### 3. Interactive API Documentation

Open your browser and visit: **http://localhost:8000/docs**

This provides a Swagger UI where you can:
- See all available endpoints
- Test the API directly from the browser
- View request/response schemas

## Neo4j Database Queries

Once you've created some family data, you can query it directly from Neo4j.

### Connecting to Neo4j

#### Option 1: Neo4j Browser (Web Interface)
1. Open **http://localhost:7474** in your browser
2. Login with credentials: `neo4j` / `password`
3. Use the query examples below in the web interface

#### Option 2: Command Line (cypher-shell)
```bash
docker exec neo4j cypher-shell -u neo4j -p password
```

### Query Examples

#### 1. View All Persons

```cypher
MATCH (n:Person) 
RETURN n.id, n.name, n.birth 
ORDER BY n.id
```

**Expected output:**
```
n.id, n.name, n.birth
"1", "John", "1970-01-01"
"2", "Jane", "1972-02-14"
"3", "Alice", "2000-05-30"
```

#### 2. View All Relationships

```cypher
MATCH (a:Person)-[r]->(b:Person) 
RETURN a.name, type(r), b.name
```

**Expected output:**
```
a.name, type(r), b.name
"John", "MARRIED", "Jane"
"John", "PARENT_OF", "Alice"
"Jane", "PARENT_OF", "Alice"
```

#### 3. Find All Parents

```cypher
MATCH (parent:Person)-[:PARENT_OF]->(child:Person)
RETURN parent.name AS Parent, child.name AS Child
ORDER BY parent.name
```

#### 4. Find All Children of a Specific Person

```cypher
MATCH (parent:Person {name: "John"})-[:PARENT_OF]->(child:Person)
RETURN child.name AS Children, child.birth AS BirthDate
```

#### 5. Find Married Couples

```cypher
MATCH (spouse1:Person)-[:MARRIED]->(spouse2:Person)
RETURN spouse1.name AS Spouse1, spouse2.name AS Spouse2
```

#### 6. Family Tree Visualization

```cypher
MATCH (n:Person)-[r]->(m:Person)
RETURN n, r, m
```

This query returns the full graph structure, which Neo4j Browser will visualize as a network diagram.

#### 7. Find Grandparents

```cypher
MATCH (grandparent:Person)-[:PARENT_OF]->(parent:Person)-[:PARENT_OF]->(grandchild:Person)
RETURN grandparent.name AS Grandparent, 
       parent.name AS Parent, 
       grandchild.name AS Grandchild
```

#### 8. Count Family Members

```cypher
MATCH (n:Person) 
RETURN count(n) AS TotalPersons
```

#### 9. Find People Born in a Specific Year

```cypher
MATCH (n:Person) 
WHERE n.birth CONTAINS "1970"
RETURN n.name, n.birth
```

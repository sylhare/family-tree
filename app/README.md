# Genealogical Tree Application
## Quick start

### Prerequisites

* [Docker](https://docs.docker.com/get-docker/) ≥ 20.10
* [Docker Compose](https://docs.docker.com/compose/) ≥ 2.x

### Run the Complete Application

1. Navigate to this folder:

   ```bash
   cd app
   ```

2. Build and start the full stack:

   ```bash
   docker compose up --build
   ```

   This will start:
   - **Web UI** at **http://localhost:3000** (Main interface)
   - **API** at **http://localhost:8000** (Backend services)
   - **Neo4j Browser** at **http://localhost:7474** (Database interface)

3. **Wait for startup** (30-60 seconds) until you see:
   ```
   genealogy-ui   | nginx/1.29.0 ... start worker processes
   genealogy-api  | Uvicorn running on http://0.0.0.0:8000
   neo4j          | Started.
   ```

## 🎯 Using the Family Tree Application

### 1. Access the Web Interface

Open your browser to **http://localhost:3000**

The interface shows:
- **API Status**: ✅ Online (green) or ❌ Offline (red)
- **Add Person Form**: Create family members
- **Add Relationship Form**: Connect family members
- **Family Tree Summary**: Live preview of your data

### 2. Add Family Members

Fill out the **Add Person** form:

```
ID: john-1          (Unique identifier)
Name: John Doe      (Full name)
Birth Date: 1970-01-01  (Optional)
```

Click **"Add Person"** - you'll see a success message and the person appears in the summary.

**Example Family:**
```
Person 1: ID: "john-1", Name: "John Doe", Birth: "1970-01-01"
Person 2: ID: "jane-1", Name: "Jane Doe", Birth: "1972-02-14"  
Person 3: ID: "alice-1", Name: "Alice Doe", Birth: "2000-05-30"
Person 4: ID: "bob-1", Name: "Bob Doe", Birth: "2002-07-15"
```

### 3. Create Relationships

Use the **Add Relationship** form to connect family members:

1. **From Person**: Select the first person
2. **Relationship Type**: Choose the relationship
   - `PARENT_OF` - Parent to child relationship
   - `MARRIED` - Spouse relationship  
   - `SIBLING` - Brother/sister relationship
   - `GRANDPARENT_OF` - Grandparent to grandchild
3. **To Person**: Select the second person

**Example Relationships:**
```
John Doe → MARRIED → Jane Doe
John Doe → PARENT_OF → Alice Doe
Jane Doe → PARENT_OF → Alice Doe
John Doe → PARENT_OF → Bob Doe
Jane Doe → PARENT_OF → Bob Doe
Alice Doe → SIBLING → Bob Doe
```

### 4. Save to Database

Once you've built your family tree:

1. Click **"Save to Neo4j"** button
2. Wait for success message: "Family tree successfully saved to Neo4j!"
3. Your data is now permanently stored in the graph database

### 5. View in Neo4j Browser

Explore your family tree in the database:

1. Open **http://localhost:7474**
2. Login: Username: `neo4j`, Password: `password`
3. Run queries to explore your data:

```cypher
// View all family members and relationships
MATCH (n) RETURN n

// Find all children of John Doe
MATCH (john:Person {name: "John Doe"})-[:PARENT_OF]->(child:Person)
RETURN john, child

// Find all married couples
MATCH (person1:Person)-[:MARRIED]-(person2:Person)
RETURN person1, person2

// View the complete family tree structure
MATCH path = (n:Person)-[*]-(m:Person)
RETURN path
```

## 🛠️ Development & API Access
### API Endpoints

- `GET /health` - Check API status
- `POST /tree` - Submit complete family tree data

### Running Tests

#### Backend Tests

Using uv (recommended)
```bash
cd app
uv sync
uv run -m pytest
```

Or using a classic virtualenv
```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

#### Frontend Tests  
```bash
cd ui
npm test              # Interactive test runner
npm run test:coverage # Generate coverage report
```

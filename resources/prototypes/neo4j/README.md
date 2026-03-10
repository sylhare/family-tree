# Neo4j Prototype

Demonstrates connecting to a Neo4j database, creating two `Person` nodes linked by a `PARENT_OF` relationship, and querying children — in Python, JavaScript, and Ruby.

## Prerequisites

Neo4j must be running. The quickest way:

```bash
docker run -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

## Environment Variables

| Variable | Default |
|---|---|
| `NEO4J_URI` | `bolt://localhost:7687` |
| `NEO4J_USER` | `neo4j` |
| `NEO4J_PASSWORD` | `password` |

## Running

### Python

```bash
pip install neo4j
python neo4j_family_tree.py
```

### JavaScript

```bash
npm install neo4j-driver
node neo4j_family_tree.js
```

### Ruby

```bash
gem install neo4j-ruby-driver   # requires Ruby >= 2.7
ruby neo4j_family_tree.rb
```

## Expected Output

```
Children of Alice: ['Bob']
```

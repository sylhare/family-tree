/**
 * Minimal Neo4j prototype: create two Person nodes + a PARENT_OF relationship,
 * then query and print children.
 *
 * Prerequisites:
 *   npm install neo4j-driver
 *   Neo4j running — see README.md
 *
 * Environment variables (optional, defaults shown):
 *   NEO4J_URI      bolt://localhost:7687
 *   NEO4J_USER     neo4j
 *   NEO4J_PASSWORD password
 */

const neo4j = require('neo4j-driver')

const URI = process.env.NEO4J_URI || 'bolt://localhost:7687'
const USER = process.env.NEO4J_USER || 'neo4j'
const PASSWORD = process.env.NEO4J_PASSWORD || 'password'

async function main() {
  const driver = neo4j.driver(URI, neo4j.auth.basic(USER, PASSWORD))
  const session = driver.session()

  try {
    // Create two Person nodes and a PARENT_OF relationship
    await session.executeWrite((tx) =>
      tx.run(
        'MERGE (p:Person {name: $parent}) ' +
        'MERGE (c:Person {name: $child}) ' +
        'MERGE (p)-[:PARENT_OF]->(c)',
        { parent: 'Alice', child: 'Bob' }
      )
    )

    // Query children
    const result = await session.executeRead((tx) =>
      tx.run(
        'MATCH (p:Person {name: $name})-[:PARENT_OF]->(c:Person) RETURN c.name AS name',
        { name: 'Alice' }
      )
    )

    const children = result.records.map((r) => r.get('name'))
    console.log('Children of Alice:', children)
  } finally {
    await session.close()
    await driver.close()
  }
}

main().catch(console.error)

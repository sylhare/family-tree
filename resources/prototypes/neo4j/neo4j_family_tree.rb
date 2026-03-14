# Minimal Neo4j prototype: create two Person nodes + a PARENT_OF relationship,
# then query and print children.
#
# Prerequisites:
#   gem install neo4j-ruby-driver   (requires Ruby >= 2.7)
#   Neo4j running — see README.md
#
# Environment variables (optional, defaults shown):
#   NEO4J_URI      bolt://localhost:7687
#   NEO4J_USER     neo4j
#   NEO4J_PASSWORD password

require 'neo4j/driver'

uri      = ENV.fetch('NEO4J_URI',      'bolt://localhost:7687')
user     = ENV.fetch('NEO4J_USER',     'neo4j')
password = ENV.fetch('NEO4J_PASSWORD', 'password')

Neo4j::Driver::GraphDatabase.driver(uri, Neo4j::Driver::AuthTokens.basic(user, password)) do |driver|
  driver.session do |session|
    # Create two Person nodes and a PARENT_OF relationship
    session.execute_write do |tx|
      tx.run(
        'MERGE (p:Person {name: $parent}) ' \
        'MERGE (c:Person {name: $child}) ' \
        'MERGE (p)-[:PARENT_OF]->(c)',
        parent: 'Alice', child: 'Bob'
      )
    end

    # Query children
    children = session.execute_read do |tx|
      result = tx.run(
        'MATCH (p:Person {name: $name})-[:PARENT_OF]->(c:Person) RETURN c.name AS name',
        name: 'Alice'
      )
      result.map { |record| record[:name] }
    end

    puts "Children of Alice: #{children}"
  end
end

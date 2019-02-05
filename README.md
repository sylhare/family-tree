# Family Tree neo4j

## Model

Here is a simple model straight from the neo4j website
![](https://github.com/Sylhare/family-tree-neo4j/blob/master/resources/img/label-property-graph-model.JPG?raw=true)

We'll start with something then make it evolve.

```js
//Creates 2 Person type node Anna and Dany in a UNION type relationship with a Union node
CREATE p =(a:Person { name:'Anna' })-[:UNION]->(:Union { name:'Wedding' })<-[:UNION]-(b:Person { name: 'Dany' })
RETURN p

// Creates the WIFE and HUSBAND relationship between Anna and Danny
MATCH (a:Person),(b:Person)
WHERE a.name = 'Anna' AND b.name = 'Dany'
CREATE (a)-[:WIFE]->(b)
CREATE (b)-[:HUSBAND]->(a)
RETURN a, b

// Find the :Union node named Wedding or using any with its ID (81 in my case) and setting the new gedcom property at U11
MATCH (a:Union)
WHERE id(a)=81 OR a.name = 'Wedding'
SET a.gedcom = 'U11'
RETURN a

// Finding the :Union node with gedcom at U11 and create a new Person node named Tim related to it as a CHILD
MATCH (a:Union)
WHERE a.gedcom = 'U11'
CREATE (:Person {name:"Tim"})-[:CHILD]->(a)
RETURN a


// Find that created note with a CHILD relation, finds any UNION in the  relation and add a SON relationship from the node Tim to them.
MATCH (a:Person { name:'Tim' })-[:CHILD]->(:Union { gedcom:'U11' })
MATCH (b:Person)-[:UNION]->(:Union { gedcom:'U11' })
CREATE (a)-[:SON]->(b)
RETURN a
```

## Neo4j

### Presentation

[Neo4j](https://neo4j.com/product/?ref=home) platform has a built-in graph database. SQL databases are like arrays, the graph database is based from node and relationships. Once installed it works similarly to any database.

Neo4j is based on 3 component:

- **Nodes** identified by labels
- **Properties** identified by property-names
- **Relations** identified by relation-types

[Neo4j](https://neo4j.com/graphacademy/)'s website is full of documentation 
to learn more about it.

You can try it in the [neo4j sandbox](https://neo4j.com/sandbox-v2/#) directly from their site. (Can be a bit slow)

### Installation

Neo4j is free and can be [downloaded](https://neo4j.com/download/) directly from their website.

Checkout neo4j's [installation doc](http://neo4j.com/docs/operations-manual/current/installation/).

> You might need to download a JVM (Open JDK or Oracle JDK).

  - Linux, the Open JDK v8
  ```
    sudo apt-get install openjdk-8-jre
  ``` 
  - On windows, you can [donwload](http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html) the Oracle JDK v8

### Cypher

[Cypher](https://neo4j.com/developer/cypher-query-language/) is the querie language for neo4j, it is an SQL-inspired language for describing patterns in graphs visually using an ascii-art syntax.

You can try the [movie example](https://neo4j.com/developer/movie-database/) by typing `:play movie graph` or you can follow this simple [gist](https://neo4j.com/developer//graphgist/34b3cf4c-da1e-4650-81e4-3a7107336ac9).

#### Nodes
Creating a node labeled `Person` with a property named `name` of value `Joe`. 

```js
CREATE (:Person {name:"Jerry"})
```
Nodes are surrounded by `( )` as a circle.

#### Relationships

Creating two different nodes like before but this time linking one to the other with a relation, typed as `KNOW` and with a property named `date`.

```js
CREATE (:Person {name:'Rick'})-[:KNOW]->(:Morty {name: "Morty", dimension: "C-137"})
CREATE (:Person {name:'Rick'})-[:KNOW {date:'2015-06-23'}]->(:Person {name: "Beth"})
```

Relation are arrows `-->`. The relationship is only one-sided

#### Query sample

Queries can use a lot of special [keywords](https://neo4j.com/docs/developer-manual/current/cypher/keyword-glossary/) and can be tweaked. Here is a simple one.

```js
MATCH (:Person)-[:KNOW]->(n:Morty)
WHERE n.dimention = "C-137" 
RETURN n
```

The `n` here define the node in the query, it is optional, here creating advance functions to display nodes.

#### APOC

[APOC](https://neo4j-contrib.github.io/neo4j-apoc-procedures/) "Awesome Procedures On Cypher" is a library of procedure to help with visualisation and data manipulation on Neo4j.

To install Apoc:

  - [Download](https://github.com/neo4j-contrib/neo4j-apoc-procedures) the latest release. And put it in the Neo4j plugin folder which place may differ:
  	- `C:\Users\username\AppData\Roaming\Neo4j Desktop\Application\neo4jDatabases\database-xxxx\installation-<version>\plugins`
  	- `C:\Program Files\Neo4j CE <version>\plugins`
  - Install the latest release from 'Neo4j Desktop' by going on a Database then [ :wrench: Manage ] then `plugin > install`.
  - Get the [package](https://www.npmjs.com/package/apoc) with npm `npm install apoc`

### Development

#### Neo4j Driver

There are multiple [options](https://neo4j.com/developer/language-guides/) to interac with Neo4j.

With python 3, you can use the pyhton driver with [py2neo](http://py2neo.org/v3/) a client library and toolkit to communicate with neo4j.

To install py2neo

    pip install py2neo
    
#### Web Framework

Neo4j works with a [REST API](https://neo4j.com/docs/rest-docs/current/), which can be used to send cypher queries and receive data.

- [Using Neo4j CYPHER queries through the REST API](https://www.grundsatzlich-it.nl/development/using-neo4j-cypher-queries-through-the-rest-api/)

Py2neo in the example works with [bottle](https://bottlepy.org/docs/dev/#) which is a micro web-framework to interac with the Neo4j database via its Rest API.

    pip install bottle
    
The librairy is also stored under Bottle.py for the example.

#### Virtualenv

[Virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/#lower-level-virtualenv) is a tool to create isolated Python environments. 
Virtualenv creates a folder which contains all the necessary executables to use the packages that a Python project would need.

    pip install virtualenv
    
Checkout the example [movie py2neo](https://github.com/neo4j-examples/movies-python-py2neo-3.0) from neo4j.
On windows to activate the cypher app rather than the (Linux) instruction from the example:

    cypher-app\Scripts\activate

### Visualisation

The default [neo4j browser](https://neo4j.com/developer/guide-neo4j-browser/) allows to display nicely the results of a Cypher query with the built-in [D3.js](https://d3js.org/) librairy.
However there are [multiple options](https://neo4j.com/developer/guide-data-visualization/) that can be used to display the graph database available on neo4j.

- More information: [D3 wiki](https://github.com/d3/d3/wiki)
- Librairy for neo4j and D3.js:  [neo4jd3](https://github.com/eisman/neo4jd3)
- Some examples:
  - An [example project](https://neo4j.com/developer/example-project/) from neo4j. 
  - [Visualizing a Network with Cypher and D3.js](https://maxdemarzi.com/2012/02/13/visualizing-a-network-with-cypher/) from Max De Marzi. [ [3d-intro](https://github.com/maxdemarzi/d3_js_intro), [3d-network](https://github.com/maxdemarzi/d3_js_network) ]
  - [visualizations of graph data with D3 and Neo4j](https://www.grundsatzlich-it.nl/development/creating-brilliant-visualizations-of-graph-data-with-d3-and-neo4j/) from Grundsatzlich.

You can use the minified 3D.js library with:
```html
 <script src="https://d3js.org/d3.v4.min.js"></script>
```

## Gedcom

[GEDCOM](https://en.wikipedia.org/wiki/GEDCOM) (an acronym standing for Genealogical Data Communication) is an open de facto specification for exchanging genealogical data between different genealogy software.

There are some gedcom parser in the resources folder.

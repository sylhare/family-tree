#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright 2011-2016, Nigel Small
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import webbrowser
from collections import deque, OrderedDict
from email.utils import parsedate_tz, mktime_tz
from warnings import warn

from py2neo.compat import integer, string
from py2neo.database.cypher import cypher_escape, cypher_repr
from py2neo.packages.httpstream import Response as HTTPResponse
from py2neo.packages.httpstream.numbers import NOT_FOUND
from py2neo.packages.neo4j.v1 import GraphDatabase
from py2neo.packages.neo4j.v1.connection import Response, RUN, PULL_ALL
from py2neo.packages.neo4j.v1.types import \
    Node as BoltNode, Relationship as BoltRelationship, Path as BoltPath, hydrated as bolt_hydrate
from py2neo.types import cast_node, Subgraph, remote
from py2neo.util import deprecated, version_tuple

from py2neo.database.auth import *
from py2neo.database.cypher import *
from py2neo.database.http import *
from py2neo.database.status import *


def normalise_request(statement, parameters, **kwparameters):

    s = ustr(statement)
    p = {}

    def add_parameters(params):
        if params:
            for k, v in dict(params).items():
                if isinstance(v, tuple):
                    v = list(v)
                p[k] = v

    add_parameters(dict(parameters or {}, **kwparameters))
    return s, p


def cypher_request(statement, parameters, **kwparameters):
    s, p = normalise_request(statement, parameters, **kwparameters)

    # OrderedDict is used here to avoid statement/parameters ordering bug
    return OrderedDict([
        ("statement", s),
        ("parameters", p),
        ("resultDataContents", ["REST"]),
    ])


class DBMS(object):
    """ Accessor for the entire database management system belonging to
    a Neo4j server installation. This corresponds to the root URI in
    the HTTP API.

    An explicit URI can be passed to the constructor::

        >>> from py2neo import DBMS
        >>> my_dbms = DBMS("http://myserver:7474/")

    Alternatively, the default value of ``http://localhost:7474/`` is
    used::

        >>> default_dbms = DBMS()
        >>> default_dbms
        <DBMS uri='http://localhost:7474/'>

    """

    __instances = {}
    __graph = None

    def __new__(cls, *uris, **settings):
        address = register_server(*uris, **settings)
        http_uri = address.http_uri("/")
        try:
            inst = cls.__instances[address]
        except KeyError:
            inst = super(DBMS, cls).__new__(cls)
            inst.address = address
            inst.__remote__ = Resource(http_uri)
            inst.__graph = None
            cls.__instances[address] = inst
        return inst

    def __repr__(self):
        return "<DBMS uri=%r>" % remote(self).uri.string

    def __eq__(self, other):
        try:
            return remote(self) == remote(other)
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(remote(self).uri)

    def __getitem__(self, database):
        return Graph(database=database, **dict(self.address))

    def __iter__(self):
        yield "data"

    def keys(self):
        return list(self)

    @property
    def graph(self):
        """ The default graph database exposed by this database management system.

        :rtype: :class:`.Graph`
        """
        return self["data"]

    def _bean_dict(self, name):
        info = Resource(remote(self).uri.string + "db/manage/server/jmx/domain/org.neo4j").get().content
        raw_config = [b for b in info["beans"] if b["name"].endswith("name=%s" % name)][0]
        d = {}
        for attribute in raw_config["attributes"]:
            name = attribute["name"]
            value = attribute.get("value")
            if value == "true":
                d[name] = True
            elif value == "false":
                d[name] = False
            else:
                try:
                    d[name] = int(value)
                except (TypeError, ValueError):
                    d[name] = value
        return d

    @property
    def database_name(self):
        """ Return the name of the active Neo4j database.
        """
        info = self._bean_dict("Kernel")
        return info.get("DatabaseName")

    @property
    def kernel_start_time(self):
        """ Return the time from which this Neo4j instance was in operational mode.
        """
        info = self._bean_dict("Kernel")
        return mktime_tz(parsedate_tz(info["KernelStartTime"]))

    @property
    def kernel_version(self):
        """ Return the version of Neo4j.
        """
        info = self._bean_dict("Kernel")
        version_string = info["KernelVersion"].partition("version:")[-1].partition(",")[0].strip()
        return version_tuple(version_string)

    @property
    def store_creation_time(self):
        """ Return the time when this Neo4j graph store was created.
        """
        info = self._bean_dict("Kernel")
        return mktime_tz(parsedate_tz(info["StoreCreationDate"]))

    @property
    def store_directory(self):
        """ Return the location of the Neo4j store.
        """
        info = self._bean_dict("Kernel")
        return info.get("StoreDirectory")

    @property
    def store_id(self):
        """ Return an identifier that, together with store creation time,
        uniquely identifies this Neo4j graph store.
        """
        info = self._bean_dict("Kernel")
        return info["StoreId"]

    @property
    def primitive_counts(self):
        """ Return a dictionary of estimates of the numbers of different
        kinds of Neo4j primitives.
        """
        return self._bean_dict("Primitive count")

    @property
    def store_file_sizes(self):
        """ Return a dictionary of file sizes for each file in the Neo4j
        graph store.
        """
        return self._bean_dict("Store file sizes")

    @property
    def config(self):
        """ Return a dictionary of the configuration parameters used to
        configure Neo4j.
        """
        return self._bean_dict("Configuration")

    @property
    def supports_auth(self):
        """ Returns :py:const:`True` if auth is supported by this
        version of Neo4j, :py:const:`False` otherwise.
        """
        return self.kernel_version >= (2, 2)

    @property
    def supports_bolt(self):
        """ Returns :py:const:`True` if Bolt is supported by this
        version of Neo4j, :py:const:`False` otherwise.
        """
        return self.kernel_version >= (3,)

    @property
    def supports_detach_delete(self):
        """ Returns :py:const:`True` if Cypher DETACH DELETE is
        supported by this version of Neo4j, :py:const:`False`
        otherwise.
        """
        return self.kernel_version >= (2, 3,)


class Graph(object):
    """ The `Graph` class represents a Neo4j graph database. Connection
    details are provided using URIs and/or individual settings. For any
    given `Graph`, the following protocol combinations are supported:

    - HTTP
    - HTTPS
    - Bolt + HTTP
    - Bolt/TLS + HTTPS

    Note that either HTTP or HTTPS must be enabled to allow for
    discovery and for some legacy features to be supported.

    The full set of `settings` supported are:

    ==============  =============================================  ==============  =============
    Keyword         Description                                    Type(s)         Default
    ==============  =============================================  ==============  =============
    ``bolt``        Use Bolt* protocol (`None` means autodetect)   bool, ``None``  ``None``
    ``secure``      Use a secure connection (Bolt/TLS + HTTPS)     bool            ``False``
    ``host``        Database server host name                      str             ``'localhost'``
    ``http_port``   Port for HTTP traffic                          int             ``7474``
    ``https_port``  Port for HTTPS traffic                         int             ``7473``
    ``bolt_port``   Port for Bolt traffic                          int             ``7687``
    ``user``        User to authenticate as                        str             ``'neo4j'``
    ``password``    Password to use for authentication             str             `no default`
    ==============  =============================================  ==============  =============

    *\* The new Bolt binary protocol is the successor to HTTP and available in Neo4j 3.0 and above.*

    Each setting can be provided as a keyword argument or as part of
    an ``http:``, ``https:`` or ``bolt:`` URI. Therefore, the examples
    below are equivalent::

        >>> from py2neo import Graph
        >>> graph_1 = Graph()
        >>> graph_2 = Graph(host="localhost")
        >>> graph_3 = Graph("http://localhost:7474/db/data/")

    Once obtained, the `Graph` instance provides direct or indirect
    access to most of the functionality available within py2neo. If
    Bolt is available (Neo4j 3.0 and above) and Bolt auto-detection
    is enabled, this will be used for Cypher queries instead of HTTP.
    """

    __instances = {}

    __schema = None
    __node_labels = None
    __relationship_types = None

    driver = None
    transaction_class = None

    def __new__(cls, *uris, **settings):
        database = settings.pop("database", "data")
        address = register_server(*uris, **settings)
        key = (cls, address, database)
        try:
            inst = cls.__instances[key]
        except KeyError:
            inst = super(Graph, cls).__new__(cls)
            inst.address = address
            inst.__remote__ = Resource(address.http_uri("/db/%s/" % database))
            inst.transaction_uri = Resource(address.http_uri("/db/%s/transaction" % database)).uri.string
            inst.transaction_class = HTTPTransaction
            use_bolt = address.bolt
            if use_bolt is None:
                use_bolt = version_tuple(inst.__remote__.get().content["neo4j_version"]) >= (3,)
            if use_bolt:
                auth = get_auth(address)
                inst.driver = GraphDatabase.driver(address.bolt_uri("/"),
                                                   auth=None if auth is None else auth.bolt_auth_token,
                                                   encypted=address.secure,
                                                   user_agent="/".join(PRODUCT))
                inst.transaction_class = BoltTransaction
            cls.__instances[key] = inst
        return inst

    def __repr__(self):
        return "<Graph uri=%r>" % remote(self).uri.string

    def __hash__(self):
        return hash(remote(self).uri)

    def __order__(self):
        return self.evaluate("MATCH (n) RETURN count(n)")

    def __size__(self):
        return self.evaluate("MATCH ()-[r]->() RETURN count(r)")

    def __len__(self):
        return self.__size__()

    def __bool__(self):
        return True

    def __nonzero__(self):
        return True

    def __contains__(self, entity):
        remote_entity = remote(entity)
        return remote_entity and remote_entity.uri.string.startswith(remote(self).uri.string)

    def begin(self, autocommit=False):
        """ Begin a new :class:`.Transaction`.

        :param autocommit: if :py:const:`True`, the transaction will
                         automatically commit after the first operation
        """
        return self.transaction_class(self, autocommit)

    def create(self, subgraph):
        """ Run a :meth:`.Transaction.create` operation within an
        `autocommit` :class:`.Transaction`.

        :param subgraph: a :class:`.Node`, :class:`.Relationship` or other
                       :class:`.Subgraph`
        """
        self.begin(autocommit=True).create(subgraph)

    @property
    def dbms(self):
        """ The database management system to which this :class:`.Graph`
        instance belongs.
        """
        return remote(self).dbms

    def degree(self, subgraph):
        """ Run a :meth:`.Transaction.degree` operation within an
        `autocommit` :class:`.Transaction`.

        :param subgraph: a :class:`.Node`, :class:`.Relationship` or other
                       :class:`.Subgraph` object
        :return: the total degree of all nodes in the subgraph
        """
        return self.begin(autocommit=True).degree(subgraph)

    def delete(self, subgraph):
        """ Run a :meth:`.Transaction.delete` operation within an
        `autocommit` :class:`.Transaction`.

        :param subgraph: a :class:`.Node`, :class:`.Relationship` or other
                       :class:`.Subgraph` object
        """
        self.begin(autocommit=True).delete(subgraph)

    def delete_all(self):
        """ Delete all nodes and relationships from this :class:`.Graph`.

        .. warning::
            This method will permanently remove **all** nodes and relationships
            from the graph and cannot be undone.
        """
        if self.dbms.supports_detach_delete:
            self.run("MATCH (a) DETACH DELETE a")
        else:
            self.run("MATCH (a) OPTIONAL MATCH (a)-[r]->() DELETE r, a")
        Node.cache.clear()
        Relationship.cache.clear()

    def evaluate(self, statement, parameters=None, **kwparameters):
        """ Run a :meth:`.Transaction.evaluate` operation within an
        `autocommit` :class:`.Transaction`.

        :param statement: Cypher statement
        :param parameters: dictionary of parameters
        :return: first value from the first record returned or
                 :py:const:`None`.
        """
        return self.begin(autocommit=True).evaluate(statement, parameters, **kwparameters)

    def exists(self, subgraph):
        """ Run a :meth:`.Transaction.exists` operation within an
        `autocommit` :class:`.Transaction`.

        :param subgraph: a :class:`.Node`, :class:`.Relationship` or other
                       :class:`.Subgraph` object
        :return:
        """
        return self.begin(autocommit=True).exists(subgraph)

    def find(self, label, property_key=None, property_value=None, limit=None):
        """ Yield all nodes with a given label, optionally filtering
        by property key and value.

        :param label: node label to match
        :param property_key: property key to match
        :param property_value: property value to match; if a tuple or set is
                               provided, any of these values may be matched
        :param limit: maximum number of nodes to match
        """
        if not label:
            raise ValueError("Empty label")
        clauses = ["MATCH (a:%s)" % cypher_escape(label)]
        parameters = {}
        if property_key is not None:
            if isinstance(property_value, (tuple, set, frozenset)):
                clauses.append("WHERE a.%s IN {x}" % cypher_escape(property_key))
                parameters["x"] = list(property_value)
            else:
                clauses.append("WHERE a.%s = {x}" % cypher_escape(property_key))
                parameters["x"] = property_value
        clauses.append("RETURN a, labels(a)")
        if limit:
            clauses.append("LIMIT %d" % limit)
        cursor = self.run("\n".join(clauses), parameters)
        while cursor.forward():
            record = cursor.current()
            a = record[0]
            a.update_labels(record[1])
            yield a
        cursor.close()

    def find_one(self, label, property_key=None, property_value=None):
        """ Find a single node by label and optional property. This method is
        intended to be used with a unique constraint and does not fail if more
        than one matching node is found.

        :param label: node label to match
        :param property_key: property key to match
        :param property_value: property value to match; if a tuple or set is
                               provided, any of these values may be matched
        """
        for node in self.find(label, property_key, property_value, limit=1):
            return node

    def _hydrate(self, data, inst=None):
        if isinstance(data, dict):
            if "errors" in data and data["errors"]:
                for error in data["errors"]:
                    raise GraphError.hydrate(error)
            elif "self" in data:
                if "type" in data:
                    return Relationship.hydrate(data, inst)
                else:
                    return Node.hydrate(data, inst)
            elif "nodes" in data and "relationships" in data:
                if "directions" not in data:
                    directions = []
                    relationships = self.evaluate(
                        "MATCH ()-[r]->() WHERE id(r) IN {x} RETURN collect(r)",
                        x=[int(uri.rpartition("/")[-1]) for uri in data["relationships"]])
                    node_uris = data["nodes"]
                    for i, relationship in enumerate(relationships):
                        if remote(relationship.start_node()).uri == node_uris[i]:
                            directions.append("->")
                        else:
                            directions.append("<-")
                    data["directions"] = directions
                return Path.hydrate(data)
            elif "results" in data:
                return self._hydrate(data["results"][0])
            elif "columns" in data and "data" in data:
                return Cursor(HTTPDataSource(self, None, data))
            elif "neo4j_version" in data:
                return self
            else:
                warn("Map literals returned over the Neo4j REST interface are ambiguous "
                     "and may be hydrated as graph objects")
                return data
        elif is_collection(data):
            return type(data)(map(self._hydrate, data))
        else:
            return data

    def match(self, start_node=None, rel_type=None, end_node=None, bidirectional=False, limit=None):
        """ Match and return all relationships with specific criteria.

        For example, to find all of Alice's friends::

            for rel in graph.match(start_node=alice, rel_type="FRIEND"):
                print(rel.end_node()["name"])

        :param start_node: start node of relationships to match (:const:`None` means any node)
        :param rel_type: type of relationships to match (:const:`None` means any type)
        :param end_node: end node of relationships to match (:const:`None` means any node)
        :param bidirectional: :const:`True` if reversed relationships should also be included
        :param limit: maximum number of relationships to match (:const:`None` means unlimited)
        """
        if start_node is None and end_node is None:
            statement = "MATCH (a)"
            parameters = {}
        elif end_node is None:
            statement = "MATCH (a) WHERE id(a)={A}"
            start_node = cast_node(start_node)
            if not remote(start_node):
                raise TypeError("Nodes for relationship match end points must be bound")
            parameters = {"A": remote(start_node)._id}
        elif start_node is None:
            statement = "MATCH (b) WHERE id(b)={B}"
            end_node = cast_node(end_node)
            if not remote(end_node):
                raise TypeError("Nodes for relationship match end points must be bound")
            parameters = {"B": remote(end_node)._id}
        else:
            statement = "MATCH (a) WHERE id(a)={A} MATCH (b) WHERE id(b)={B}"
            start_node = cast_node(start_node)
            end_node = cast_node(end_node)
            if not remote(start_node) or not remote(end_node):
                raise TypeError("Nodes for relationship match end points must be bound")
            parameters = {"A": remote(start_node)._id, "B": remote(end_node)._id}
        if rel_type is None:
            rel_clause = ""
        elif is_collection(rel_type):
            rel_clause = ":" + "|:".join("`{0}`".format(_) for _ in rel_type)
        else:
            rel_clause = ":`{0}`".format(rel_type)
        if bidirectional:
            statement += " MATCH (a)-[r" + rel_clause + "]-(b) RETURN r"
        else:
            statement += " MATCH (a)-[r" + rel_clause + "]->(b) RETURN r"
        if limit is not None:
            statement += " LIMIT {0}".format(int(limit))
        cursor = self.run(statement, parameters)
        while cursor.forward():
            record = cursor.current()
            yield record["r"]

    def match_one(self, start_node=None, rel_type=None, end_node=None, bidirectional=False):
        """ Match and return one relationship with specific criteria.

        :param start_node: start node of relationships to match (:const:`None` means any node)
        :param rel_type: type of relationships to match (:const:`None` means any type)
        :param end_node: end node of relationships to match (:const:`None` means any node)
        :param bidirectional: :const:`True` if reversed relationships should also be included
        """
        rels = list(self.match(start_node, rel_type, end_node,
                               bidirectional, 1))
        if rels:
            return rels[0]
        else:
            return None

    def merge(self, subgraph, label=None, *property_keys):
        """ Run a :meth:`.Transaction.merge` operation within an
        `autocommit` :class:`.Transaction`.

        :param subgraph: a :class:`.Node`, :class:`.Relationship` or other
                       :class:`.Subgraph` object
        :param label: label on which to match any existing nodes
        :param property_keys: property keys on which to match any existing nodes
        """
        self.begin(autocommit=True).merge(subgraph, label, *property_keys)

    @property
    @deprecated("Graph.neo4j_version is deprecated, use DBMS.kernel_version instead")
    def neo4j_version(self):
        return version_tuple(remote(self).metadata["neo4j_version"])

    def node(self, id_):
        """ Fetch a node by ID. This method creates an object representing the
        remote node with the ID specified but fetches no data from the server.
        For this reason, there is no guarantee that the entity returned
        actually exists.

        :param id_:
        """
        resource = remote(self).resolve("node/%s" % id_)
        uri_string = resource.uri.string
        try:
            return Node.cache[uri_string]
        except KeyError:
            node = self.evaluate("MATCH (a) WHERE id(a)={x} RETURN a", x=id_)
            if node is None:
                raise IndexError("Node %d not found" % id_)
            else:
                return node

    @property
    def node_labels(self):
        """ The set of node labels currently defined within the graph.
        """
        if self.__node_labels is None:
            self.__node_labels = Resource(remote(self).uri.string + "labels")
        return frozenset(self.__node_labels.get().content)

    def open_browser(self):
        """ Open a page in the default system web browser pointing at
        the Neo4j browser application for this graph.
        """
        webbrowser.open(remote(self.dbms).uri.string)

    def pull(self, subgraph):
        """ Pull data to one or more entities from their remote counterparts.

        :param subgraph: the collection of nodes and relationships to pull
        """
        try:
            subgraph.__db_pull__(self)
        except AttributeError:
            raise TypeError("No method defined to pull object %r" % subgraph)

    def push(self, subgraph):
        """ Push data from one or more entities to their remote counterparts.

        :param subgraph: the collection of nodes and relationships to push
        """
        try:
            subgraph.__db_push__(self)
        except AttributeError:
            raise TypeError("No method defined to push object %r" % subgraph)

    def relationship(self, id_):
        """ Fetch a relationship by ID.

        :param id_:
        """
        resource = remote(self).resolve("relationship/" + str(id_))
        uri_string = resource.uri.string
        try:
            return Relationship.cache[uri_string]
        except KeyError:
            relationship = self.evaluate("MATCH ()-[r]->() WHERE id(r)={x} RETURN r", x=id_)
            if relationship is None:
                raise IndexError("Relationship %d not found" % id_)
            else:
                return relationship

    @property
    def relationship_types(self):
        """ The set of relationship types currently defined within the graph.
        """
        if self.__relationship_types is None:
            self.__relationship_types = Resource(remote(self).uri.string + "relationship/types")
        return frozenset(self.__relationship_types.get().content)

    def run(self, statement, parameters=None, **kwparameters):
        """ Run a :meth:`.Transaction.run` operation within an
        `autocommit` :class:`.Transaction`.

        :param statement: Cypher statement
        :param parameters: dictionary of parameters
        :return:
        """
        return self.begin(autocommit=True).run(statement, parameters, **kwparameters)

    def separate(self, subgraph):
        """ Run a :meth:`.Transaction.separate` operation within an
        `autocommit` :class:`.Transaction`.

        :param subgraph: a :class:`.Node`, :class:`.Relationship` or other
                       :class:`.Subgraph`
        """
        self.begin(autocommit=True).separate(subgraph)

    @property
    def schema(self):
        """ The schema resource for this graph.

        :rtype: :class:`Schema`
        """
        if self.__schema is None:
            self.__schema = Schema(remote(self).uri.string + "schema")
        return self.__schema


class Schema(object):
    """ The schema resource attached to a `Graph` instance.
    """

    def __init__(self, uri):
        self._index_template = ResourceTemplate(uri + "/index/{label}")
        self._index_key_template = ResourceTemplate(uri + "/index/{label}/{property_key}")
        self._uniqueness_constraint_template = \
            ResourceTemplate(uri + "/constraint/{label}/uniqueness")
        self._uniqueness_constraint_key_template = \
            ResourceTemplate(uri + "/constraint/{label}/uniqueness/{property_key}")

    def create_index(self, label, property_key):
        """ Create a schema index for a label and property
        key combination.
        """
        self._index_template.expand(label=label).post({"property_keys": [property_key]})

    def create_uniqueness_constraint(self, label, property_key):
        """ Create a uniqueness constraint for a label.
        """
        self._uniqueness_constraint_template.expand(label=label).post(
            {"property_keys": [property_key]})

    def drop_index(self, label, property_key):
        """ Remove label index for a given property key.
        """
        try:
            self._index_key_template.expand(label=label, property_key=property_key).delete()
        except GraphError as error:
            cause = error.__cause__
            if isinstance(cause, HTTPResponse):
                if cause.status_code == NOT_FOUND:
                    raise GraphError("No such schema index (label=%r, key=%r)" % (
                        label, property_key))
            raise

    def drop_uniqueness_constraint(self, label, property_key):
        """ Remove the uniqueness constraint for a given property key.
        """
        try:
            self._uniqueness_constraint_key_template.expand(
                label=label, property_key=property_key).delete()
        except GraphError as error:
            cause = error.__cause__
            if isinstance(cause, HTTPResponse):
                if cause.status_code == NOT_FOUND:
                    raise GraphError("No such unique constraint (label=%r, key=%r)" % (
                        label, property_key))
            raise

    def get_indexes(self, label):
        """ Fetch a list of indexed property keys for a label.
        """
        return [
            indexed["property_keys"][0]
            for indexed in self._index_template.expand(label=label).get().content
        ]

    def get_uniqueness_constraints(self, label):
        """ Fetch a list of unique constraints for a label.
        """

        return [
            unique["property_keys"][0]
            for unique in self._uniqueness_constraint_template.expand(label=label).get().content
        ]


class DataSource(object):

    def keys(self):
        """ Return the keys for the whole data set.
        """

    def fetch(self):
        """ Fetch and return the next item.
        """


class HTTPDataSource(DataSource):

    def __init__(self, graph, transaction, data=None):
        self.graph = graph
        self.transaction = transaction
        self._keys = None
        self.buffer = deque()
        self.loaded = False
        if data:
            self.load(data)

    def keys(self):
        if not self.loaded:
            self.transaction.process()
        return self._keys

    def fetch(self):
        try:
            return self.buffer.popleft()
        except IndexError:
            if self.loaded:
                return None
            else:
                self.transaction.process()
                return self.fetch()

    def load(self, data):
        assert not self.loaded
        try:
            entities = self.transaction.entities.popleft()
        except (AttributeError, IndexError):
            entities = {}
        self._keys = keys = tuple(data["columns"])
        hydrate = self.graph._hydrate
        for record in data["data"]:
            values = []
            for i, value in enumerate(record["rest"]):
                key = keys[i]
                cached = entities.get(key)
                values.append(hydrate(value, inst=cached))
            self.buffer.append(Record(keys, values))
        self.loaded = True


class BoltDataSource(DataSource):

    def __init__(self, connection, entities, graph_uri):
        self.connection = connection
        self.entities = entities
        self.graph_uri = graph_uri
        self._keys = None
        self.buffer = deque()
        self.loaded = False

    def keys(self):
        self.connection.send()
        while self._keys is None and not self.loaded:
            self.connection.fetch()
        return self._keys

    def fetch(self):
        try:
            return self.buffer.popleft()
        except IndexError:
            if self.loaded:
                return None
            else:
                self.connection.send()
                while not self.buffer and not self.loaded:
                    self.connection.fetch()
                return self.fetch()

    def on_header(self, metadata):
        """ Called on receipt of the result header.

        :param metadata:
        """
        self._keys = metadata["fields"]

    def on_record(self, values):
        """ Called on receipt of each result record.

        :param values:
        """
        keys = self._keys
        hydrated_values = []
        for i, value in enumerate(values):
            key = keys[i]
            cached = self.entities.get(key)
            v = self.rehydrate(bolt_hydrate(value), inst=cached)
            hydrated_values.append(v)
        self.buffer.append(Record(keys, hydrated_values))

    def on_footer(self, metadata):
        """ Called on receipt of the result footer.

        :param metadata:
        """
        self.loaded = True
        # TODO: summary data
        #cursor.summary = ResultSummary(self.statement, self.parameters, **metadata)

    def on_failure(self, metadata):
        """ Called on execution failure.

        :param metadata:
        """
        raise GraphError.hydrate(metadata)

    def rehydrate(self, obj, inst=None):
        # TODO: hydrate directly instead of via HTTP hydration
        if isinstance(obj, BoltNode):
            return Node.hydrate({
                "self": "%snode/%d" % (self.graph_uri, obj.id),
                "metadata": {"labels": list(obj.labels)},
                "data": obj.properties,
            }, inst)
        elif isinstance(obj, BoltRelationship):
            return Relationship.hydrate({
                "self": "%srelationship/%d" % (self.graph_uri, obj.id),
                "start": "%snode/%d" % (self.graph_uri, obj.start),
                "end": "%snode/%d" % (self.graph_uri, obj.end),
                "type": obj.type,
                "data": obj.properties,
            }, inst)
        elif isinstance(obj, BoltPath):
            return Path.hydrate({
                "nodes": ["%snode/%d" % (self.graph_uri, n.id) for n in obj.nodes],
                "relationships": ["%srelationship/%d" % (self.graph_uri, r.id)
                                  for r in obj.relationships],
                "directions": ["->" if r.start == obj.nodes[i].id else "<-"
                               for i, r in enumerate(obj.relationships)],
            })
        elif isinstance(obj, list):
            return list(map(self.rehydrate, obj))
        elif isinstance(obj, dict):
            return {key: self.rehydrate(value) for key, value in obj.items()}
        else:
            return obj


class TransactionFinished(GraphError):
    """ Raised when actions are attempted against a :class:`.Transaction`
    that is no longer available for use.
    """


class Transaction(object):
    """ A transaction is a transient resource that allows multiple Cypher
    statements to be executed within a single server transaction.
    """

    def __init__(self, graph, autocommit=False):
        self.graph = graph
        self.autocommit = autocommit
        self._finished = False
        self.entities = deque()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

    def _assert_unfinished(self):
        if self._finished:
            raise TransactionFinished(self)

    def finished(self):
        """ Indicates whether or not this transaction has been completed
        or is still open.
        """
        return self._finished

    def run(self, statement, parameters=None, **kwparameters):
        """ Add a statement to the current queue of statements to be
        executed.

        :param statement: Cypher statement
        :param parameters: dictionary of parameters
        """

    @deprecated("Transaction.append(...) is deprecated, use Transaction.run(...) instead")
    def append(self, statement, parameters=None, **kwparameters):
        return self.run(statement, parameters, **kwparameters)

    def _post(self, commit=False):
        pass

    def process(self):
        """ Send all pending statements to the server for execution, leaving
        the transaction open for further statements.
        """
        self._post()

    def finish(self):
        self._assert_unfinished()
        self._finished = True

    def commit(self):
        """ Send all pending statements to the server for execution and commit
        the transaction.
        """
        self._post(commit=True)

    def rollback(self):
        """ Rollback the current transaction, undoing all actions taken so far.
        """

    def evaluate(self, statement, parameters=None, **kwparameters):
        """ Execute a single Cypher statement and return the value from
        the first column of the first record.

        :param statement: Cypher statement
        :param parameters: dictionary of parameters
        :returns: single return value or :const:`None`
        """
        return self.run(statement, parameters, **kwparameters).evaluate(0)

    def create(self, subgraph):
        """ Create remote nodes and relationships that correspond to those in a
        local subgraph. Any entities in *subgraph* that are already bound to
        remote entities will remain unchanged, those which are not will become
        bound to their newly-created counterparts.

        For example::

            >>> from py2neo import Graph, Node, Relationship
            >>> g = Graph()
            >>> tx = g.begin()
            >>> a = Node("Person", name="Alice")
            >>> tx.create(a)
            >>> b = Node("Person", name="Bob")
            >>> ab = Relationship(a, "KNOWS", b)
            >>> tx.create(ab)
            >>> tx.commit()
            >>> g.exists(ab)
            True

        :param subgraph: a :class:`.Node`, :class:`.Relationship` or other
                    creatable object
        """
        try:
            subgraph.__db_create__(self)
        except AttributeError:
            raise TypeError("No method defined to create object %r" % subgraph)

    def degree(self, subgraph):
        """ Return the total number of relationships attached to all nodes in
        a subgraph.

        :param subgraph: a :class:`.Node`, :class:`.Relationship` or other
                       :class:`.Subgraph`
        :returns: the total number of distinct relationships
        """
        try:
            return subgraph.__db_degree__(self)
        except AttributeError:
            raise TypeError("No method defined to determine the degree of object %r" % subgraph)

    def delete(self, subgraph):
        """ Delete the remote nodes and relationships that correspond to
        those in a local subgraph.

        :param subgraph: a :class:`.Node`, :class:`.Relationship` or other
                       :class:`.Subgraph`
        """
        try:
            subgraph.__db_delete__(self)
        except AttributeError:
            raise TypeError("No method defined to delete object %r" % subgraph)

    def exists(self, subgraph):
        """ Determine whether one or more graph entities all exist within the
        database. Note that if any nodes or relationships in *subgraph* are not
        bound to remote counterparts, this method will return ``False``.

        :param subgraph: a :class:`.Node`, :class:`.Relationship` or other
                       :class:`.Subgraph`
        :returns: ``True`` if all entities exist remotely, ``False`` otherwise
        """
        try:
            return subgraph.__db_exists__(self)
        except AttributeError:
            raise TypeError("No method defined to determine the existence of object %r" % subgraph)

    def merge(self, subgraph, primary_label=None, primary_key=None):
        """ Merge nodes and relationships from a local subgraph into the
        database. Each node and relationship is merged independently, with
        nodes merged first and relationships merged second.

        For each node, the merge is carried out by comparing that node with a
        potential remote equivalent on the basis of a label and property value.
        If no remote match is found, a new node is created. The label and
        property to use for comparison are determined by `primary_label` and
        `primary_key` but may be overridden for individual nodes by the
        presence of `__primarylabel__` and `__primarykey__` attributes on
        the node itself. Note that multiple property keys may be specified by
        using a tuple.

        For each relationship, the merge is carried out by comparing that
        relationship with a potential remote equivalent on the basis of matching
        start and end nodes plus relationship type. If no remote match is found,
        a new relationship is created.

        :param subgraph: a :class:`.Node`, :class:`.Relationship` or other
                       :class:`.Subgraph` object
        :param primary_label: label on which to match any existing nodes
        :param primary_key: property key(s) on which to match any existing
                            nodes
        """
        try:
            subgraph.__db_merge__(self, primary_label, primary_key)
        except AttributeError:
            raise TypeError("No method defined to merge object %r" % subgraph)

    def separate(self, subgraph):
        """ Delete the remote relationships that correspond to those in a local
        subgraph. This leaves any nodes untouched.

        :param subgraph: a :class:`.Node`, :class:`.Relationship` or other
                       :class:`.Subgraph`
        """
        try:
            subgraph.__db_separate__(self)
        except AttributeError:
            raise TypeError("No method defined to separate object %r" % subgraph)


class HTTPTransaction(Transaction):
    """ A transaction is a transient resource that allows multiple Cypher
    statements to be executed within a single server transaction.
    """

    def __init__(self, graph, autocommit=False):
        Transaction.__init__(self, graph, autocommit)
        self.statements = []
        self.sources = []
        uri = graph.transaction_uri
        self._begin = Resource(uri)
        self._begin_commit = Resource(uri + "/commit")
        self._execute = None
        self._commit = None

    def run(self, statement, parameters=None, **kwparameters):
        self._assert_unfinished()
        self.statements.append(cypher_request(statement, parameters, **kwparameters))
        source = HTTPDataSource(self.graph, self)
        cursor = Cursor(source)
        self.sources.append(source)
        if self.autocommit:
            self.commit()
        return cursor

    def _post(self, commit=False):
        self._assert_unfinished()
        if commit:
            resource = self._commit or self._begin_commit
            self.finish()
        else:
            resource = self._execute or self._begin
        rs = resource.post({"statements": self.statements})
        location = rs.location
        if location:
            self._execute = Resource(location)
        raw = rs.content
        rs.close()
        self.statements = []
        if "commit" in raw:
            self._commit = Resource(raw["commit"])
        for raw_error in raw["errors"]:
            raise GraphError.hydrate(raw_error)
        for raw_result in raw["results"]:
            source = self.sources.pop(0)
            source.load(raw_result)

    def rollback(self):
        self._assert_unfinished()
        try:
            if self._execute:
                self._execute.delete()
        finally:
            self.finish()


class BoltTransaction(Transaction):

    def __init__(self, graph, autocommit=False):
        Transaction.__init__(self, graph, autocommit)
        self.driver = driver = self.graph.driver
        self.session = driver.session()
        self.sources = []
        if not self.autocommit:
            self.run("BEGIN")

    def run(self, statement, parameters=None, **kwparameters):
        self._assert_unfinished()
        connection = self.session.connection
        try:
            entities = self.entities.popleft()
        except IndexError:
            entities = {}
        source = BoltDataSource(connection, entities, remote(self.graph).uri.string)

        run_response = Response(connection)
        run_response.on_success = source.on_header
        run_response.on_failure = source.on_failure

        pull_all_response = Response(connection)
        pull_all_response.on_record = source.on_record
        pull_all_response.on_success = source.on_footer
        pull_all_response.on_failure = source.on_failure

        s, p = normalise_request(statement, parameters, **kwparameters)
        connection.append(RUN, (s, p), run_response)
        connection.append(PULL_ALL, (), pull_all_response)
        self.sources.append(source)
        if self.autocommit:
            self.finish()
        return Cursor(source)

    def _sync(self):
        connection = self.session.connection
        connection.send()
        while self.sources:
            source = self.sources.pop(0)
            while not source.loaded:
                connection.fetch()

    def _post(self, commit=False):
        if commit:
            self.run("COMMIT")
            self.finish()
        else:
            self._sync()

    def finish(self):
        self._sync()
        Transaction.finish(self)
        self.session.close()
        self.session = None

    def rollback(self):
        self._assert_unfinished()
        try:
            self.run("ROLLBACK")
            self._sync()
        finally:
            self.finish()


class Cursor(object):
    """ A `Cursor` is a navigator for a stream of records.

    A cursor can be thought of as a window onto an underlying data
    stream. All cursors in py2neo are "forward-only", meaning that
    navigation starts before the first record and may proceed only in a
    forward direction.

    It is not generally necessary for application code to instantiate a
    cursor directly as one will be returned by any Cypher execution method.
    However, cursor creation requires only a :class:`.DataSource` object
    which contains the logic for how to access the source data that the
    cursor navigates.

    Many simple cursor use cases require only the :meth:`.forward` method
    and the :attr:`.current` attribute. To navigate through all available
    records, a `while` loop can be used::

        while cursor.forward():
            print(cursor.current["name"])

    If only the first record is of interest, a similar `if` structure will
    do the job::

        if cursor.forward():
            print(cursor.current["name"])

    To combine `forward` and `current` into a single step, use :attr:`.next`::

        print(cursor.next["name"])

    Cursors are also iterable, so can be used in a loop::

        for record in cursor:
            print(record["name"])

    For queries that are expected to return only a single value within a
    single record, use the :meth:`.evaluate` method. This will return the
    first value from the next record or :py:const:`None` if neither the
    field nor the record are present::

        print(cursor.evaluate())

    """

    def __init__(self, source):
        self._source = source
        self._current = None

    def __next__(self):
        if self.forward():
            return self._current
        else:
            raise StopIteration()

    def __iter__(self):
        while self.forward():
            yield self._current

    def current(self):
        """ Returns the current record or :py:const:`None` if no record
        has yet been selected.
        """
        return self._current

    def next(self):
        """ Returns the next record in the stream, or raises
        :py:class:`StopIteration` if no more records are available.

            cursor.current if cursor.forward() else None

        """
        return self.__next__()

    def close(self):
        """ Close this cursor and free up all associated resources.
        """
        self._source = None
        self._current = None

    def keys(self):
        """ Return the field names for the records in the stream.
        """
        return self._source.keys()

    def forward(self, amount=1):
        """ Attempt to move the cursor one position forward (or by
        another amount if explicitly specified). The cursor will move
        position by up to, but never more than, the amount specified.
        If not enough scope for movement remains, only that remainder
        will be consumed. The total amount moved is returned.

        :param amount: the amount to move the cursor
        :returns: the amount that the cursor was able to move
        """
        if amount == 0:
            return 0
        assert amount > 0
        amount = int(amount)
        moved = 0
        fetch = self._source.fetch
        while moved != amount:
            new_current = fetch()
            if new_current is None:
                break
            else:
                self._current = new_current
                moved += 1
        return moved

    def evaluate(self, field=0):
        """ Return the value of the first field from the next record
        (or the value of another field if explicitly specified).

        This method attempts to move the cursor one step forward and,
        if successful, selects and returns an individual value from
        the new current record. By default, this value will be taken
        from the first value in that record but this can be overridden
        with the `field` argument, which can represent either a
        positional index or a textual key.

        If the cursor cannot be moved forward or if the record contains
        no values, :py:const:`None` will be returned instead.

        This method is particularly useful when it is known that a
        Cypher query returns only a single value.

        :param field: field to select value from (optional)
        :returns: value of the field or :py:const:`None`

        Example:
            >>> from py2neo import Graph
            >>> g = Graph()
            >>> g.run("MATCH (a) WHERE a.email={x} RETURN a.name", x="bob@acme.com").evaluate()
            'Bob Robertson'
        """
        if self.forward():
            try:
                return self._current[field]
            except IndexError:
                return None
        else:
            return None

    def dump(self, out=stdout):
        """ Consume all records from this cursor and write in tabular
        form to the console.

        :param out: the channel to which output should be dumped
        """
        records = list(self)
        keys = self.keys()
        widths = [len(key) for key in keys]
        for record in records:
            for i, value in enumerate(record):
                widths[i] = max(widths[i], len(ustr(value)))
        templates = [u" {:%d} " % width for width in widths]
        out.write(u"".join(templates[i].format(key) for i, key in enumerate(keys)))
        out.write(u"\n")
        out.write(u"".join("-" * (width + 2) for width in widths))
        out.write(u"\n")
        for i, record in enumerate(records):
            out.write(u"".join(templates[i].format(ustr(value)) for i, value in enumerate(record)))
            out.write(u"\n")


class Record(tuple, Subgraph):

    def __new__(cls, keys, values):
        if len(keys) == len(values):
            return super(Record, cls).__new__(cls, values)
        else:
            raise ValueError("Keys and values must be of equal length")

    def __init__(self, keys, values):
        self.__keys = tuple(keys)
        nodes = []
        relationships = []
        for value in values:
            if hasattr(value, "nodes"):
                nodes.extend(value.nodes())
            if hasattr(value, "relationships"):
                relationships.extend(value.relationships())
        Subgraph.__init__(self, nodes, relationships)
        self.__repr = None

    def __repr__(self):
        r = self.__repr
        if r is None:
            s = ["("]
            for i, key in enumerate(self.__keys):
                if i > 0:
                    s.append(", ")
                s.append(repr(key))
                s.append(": ")
                s.append(repr(self[i]))
            s.append(")")
            r = self.__repr = "".join(s)
        return r

    def __getitem__(self, item):
        if isinstance(item, string):
            try:
                return tuple.__getitem__(self, self.__keys.index(item))
            except ValueError:
                raise KeyError(item)
        elif isinstance(item, slice):
            return self.__class__(self.__keys[item.start:item.stop],
                                  tuple.__getitem__(self, item))
        else:
            return tuple.__getitem__(self, item)

    def __getslice__(self, i, j):
        return self.__class__(self.__keys[i:j], tuple.__getslice__(self, i, j))

    def keys(self):
        return self.__keys

    def values(self):
        return tuple(self)

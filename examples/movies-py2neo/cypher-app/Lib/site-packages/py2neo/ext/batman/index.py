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


from py2neo.database import Graph, Resource, ResourceTemplate
from py2neo.types import Node, Relationship, remote
from py2neo.packages.httpstream.numbers import CREATED
from py2neo.packages.httpstream.packages.urimagic import percent_encode, URI

from .batch import ManualIndexWriteBatch


class ManualIndexManager(object):

    def __init__(self, graph):
        self.graph = graph
        self._indexes = {Node: {}, Relationship: {}}

    def _index_manager(self, content_type):
        """ Fetch the index management resource for the given `content_type`.

        :param content_type:
        :return:
        """
        if content_type is Node:
            uri = remote(self.graph).metadata["node_index"]
        elif content_type is Relationship:
            uri = remote(self.graph).metadata["relationship_index"]
        else:
            raise TypeError("Indexes can manage either Nodes or Relationships")
        return Resource(uri)

    def get_indexes(self, content_type):
        """ Fetch a dictionary of all available indexes of a given type.

        :param content_type: either :class:`.Node` or
            :class:`.Relationship`
        :return: a list of :class:`.ManualIndex` instances of the specified type
        """
        index_manager = self._index_manager(content_type)
        index_index = index_manager.get().content
        if index_index:
            self._indexes[content_type] = dict(
                (key, ManualIndex(content_type, value["template"]))
                for key, value in index_index.items()
            )
        else:
            self._indexes[content_type] = {}
        return self._indexes[content_type]

    def get_index(self, content_type, index_name):
        """ Fetch a specific index from the current database, returning an
        :class:`.ManualIndex` instance. If an index with the supplied `name` and
        content `type` does not exist, :py:const:`None` is returned.

        :param content_type: either :class:`.Node` or
            :class:`.Relationship`
        :param index_name: the name of the required index
        :return: an :class:`.ManualIndex` instance or :py:const:`None`
        """
        if index_name not in self._indexes[content_type]:
            self.get_indexes(content_type)
        if index_name in self._indexes[content_type]:
            return self._indexes[content_type][index_name]
        else:
            return None

    def get_or_create_index(self, content_type, index_name, config=None):
        """ Fetch a specific index from the current database, returning an
        :class:`.ManualIndex` instance. If an index with the supplied `name` and
        content `type` does not exist, one is created with either the
        default configuration or that supplied in `config`.

        :param content_type: either :class:`.Node` or
            :class:`.Relationship`
        :param index_name: the name of the required index
        :return: a :class:`.ManualIndex` instance
        """
        index = self.get_index(content_type, index_name)
        if index:
            return index
        index_manager = self._index_manager(content_type)
        rs = index_manager.post({"name": index_name, "config": config or {}})
        index = ManualIndex(content_type, rs.content["template"])
        self._indexes[content_type].update({index_name: index})
        return index

    def delete_index(self, content_type, index_name):
        """ Delete the entire index identified by the type and name supplied.

        :param content_type: either :class:`.Node` or
            :class:`.Relationship`
        :param index_name: the name of the index to delete
        :raise LookupError: if the specified index does not exist
        """
        if index_name not in self._indexes[content_type]:
            self.get_indexes(content_type)
        if index_name in self._indexes[content_type]:
            index = self._indexes[content_type][index_name]
            remote(index).delete()
            del self._indexes[content_type][index_name]
        else:
            raise LookupError("Index not found")

    def get_indexed_node(self, index_name, key, value):
        """ Fetch the first node indexed with the specified details, returning
        :py:const:`None` if none found.

        :param index_name: the name of the required index
        :param key: the index key
        :param value: the index value
        :return: a :py:class:`Node` instance
        """
        index = self.get_index(Node, index_name)
        if index:
            nodes = index.get(key, value)
            if nodes:
                return nodes[0]
        return None

    def get_or_create_indexed_node(self, index_name, key, value, properties=None):
        """ Fetch the first node indexed with the specified details, creating
        and returning a new indexed node if none found.

        :param index_name: the name of the required index
        :param key: the index key
        :param value: the index value
        :param properties: properties for the new node, if one is created
            (optional)
        :return: a :py:class:`Node` instance
        """
        index = self.get_or_create_index(Node, index_name)
        return index.get_or_create(key, value, properties or {})

    def get_indexed_relationship(self, index_name, key, value):
        """ Fetch the first relationship indexed with the specified details,
        returning :py:const:`None` if none found.

        :param index_name: the name of the required index
        :param key: the index key
        :param value: the index value
        :return: a :py:class:`Relationship` instance
        """
        index = self.get_index(Relationship, index_name)
        if index:
            relationships = index.get(key, value)
            if relationships:
                return relationships[0]
        return None


class ManualIndex(object):
    """ Searchable database index which can contain either nodes or
    relationships.
    """

    def __init__(self, content_type, uri, name=None):
        self._content_type = content_type
        key_value_pos = uri.find("/{key}/{value}")
        if key_value_pos >= 0:
            self._searcher = ResourceTemplate(uri)
            self.__remote__ = Resource(uri[:key_value_pos])
        else:
            self.__remote__ = Resource(uri)
            self._searcher = ResourceTemplate(uri.string + "/{key}/{value}")
        uri = remote(self).uri
        self._create_or_fail = Resource(uri.resolve("?uniqueness=create_or_fail"))
        self._get_or_create = Resource(uri.resolve("?uniqueness=get_or_create"))
        self._query_template = ResourceTemplate(uri.string + "{?query,order}")
        self._name = name or uri.path.segments[-1]
        self.__searcher_stem_cache = {}
        self.graph = Graph(uri.resolve("/db/data/").string)

    def __repr__(self):
        return "{0}({1}, {2})".format(
            self.__class__.__name__,
            self._content_type.__name__,
            repr(remote(self).uri.string)
        )

    def _searcher_stem_for_key(self, key):
        if key not in self.__searcher_stem_cache:
            stem = self._searcher.uri_template.string.partition("{key}")[0]
            self.__searcher_stem_cache[key] = stem + percent_encode(key) + "/"
        return self.__searcher_stem_cache[key]

    def add(self, key, value, entity):
        """ Add an entity to this index under the `key`:`value` pair supplied.

        Note that while Neo4j indexes allow multiple entities to be added under
        a particular key:value, the same entity may only be represented once;
        this method is therefore idempotent.

        :param key:
        :param value:
        :param entity:
        """
        remote(self).post({
            "key": key,
            "value": value,
            "uri": remote(entity).uri.string,
        })
        return entity

    def add_if_none(self, key, value, entity):
        """ Add an entity to this index under the `key`:`value` pair
        supplied if no entry already exists at that point.

        If added, this method returns the entity, otherwise :py:const:`None`
        is returned.
        """
        rs = self._get_or_create.post({
            "key": key,
            "value": value,
            "uri": remote(entity).uri.string,
        })
        if rs.status_code == CREATED:
            return entity
        else:
            return None

    @property
    def content_type(self):
        """ Return the type of entity contained within this index. Will return
        either :py:class:`Node` or :py:class:`Relationship`.
        """
        return self._content_type

    @property
    def name(self):
        """ Return the name of this index.
        """
        return self._name

    def get(self, key, value):
        """ Fetch a list of all entities from the index which are associated
        with the `key`:`value` pair supplied.

        :param key:
        :param value:
        """
        return [
            self.graph._hydrate(result)
            for result in self._searcher.expand(key=key, value=value).get().content
        ]

    def create(self, key, value, abstract):
        """ Create and index a new node or relationship using the abstract
        provided.

        :param key:
        :param value:
        :param abstract:
        """
        batch = ManualIndexWriteBatch(self.graph)
        if self._content_type is Node:
            batch.create(abstract)
            batch.add_to_index(Node, self, key, value, 0)
        elif self._content_type is Relationship:
            batch.create(abstract)
            batch.add_to_index(Relationship, self, key, value, 0)
        else:
            raise TypeError(self._content_type)
        entity, index_entry = batch.run()
        return entity

    def _create_unique(self, key, value, abstract):
        """ Internal method to support `get_or_create` and `create_if_none`.
        """
        if self._content_type is Node:
            body = {
                "key": key,
                "value": value,
                "properties": abstract
            }
        elif self._content_type is Relationship:
            body = {
                "key": key,
                "value": value,
                "start": abstract[0].uri.string,
                "type": abstract[1],
                "end": abstract[2].uri.string,
                "properties": abstract[3] if len(abstract) > 3 else None
            }
        else:
            raise TypeError(self._content_type)
        return self._get_or_create.post(body)

    def get_or_create(self, key, value, abstract):
        """ Fetch a single entity from the index which is associated with the
        `key`:`value` pair supplied, creating a new entity with the supplied
        details if none exists.
        """
        return self.graph._hydrate(self._create_unique(key, value, abstract).content)

    def create_if_none(self, key, value, abstract):
        """ Create a new entity with the specified details within the current
        index, under the `key`:`value` pair supplied, if no such entity already
        exists. If creation occurs, the new entity will be returned, otherwise
        :py:const:`None` will be returned.
        """
        rs = self._create_unique(key, value, abstract)
        if rs.status_code == CREATED:
            return self.graph._hydrate(rs.content)
        else:
            return None

    def remove(self, key=None, value=None, entity=None):
        """ Remove any entries from the index which match the parameters
        supplied. The allowed parameter combinations are:

        `key`, `value`, `entity`
            remove a specific entity indexed under a given key-value pair

        `key`, `value`
            remove all entities indexed under a given key-value pair

        `key`, `entity`
            remove a specific entity indexed against a given key but with
            any value

        `entity`
            remove all occurrences of a specific entity regardless of
            key and value

        """
        if key and value and entity:
            t = ResourceTemplate(remote(self).uri.string + "/{key}/{value}/{entity}")
            t.expand(key=key, value=value, entity=remote(entity)._id).delete()
        elif key and value:
            uris = [
                URI(remote(entity).metadata["indexed"])
                for entity in self.get(key, value)
            ]
            batch = ManualIndexWriteBatch(self.graph)
            for uri in uris:
                batch.append_delete(uri)
            batch.run()
        elif key and entity:
            t = ResourceTemplate(remote(self).uri.string + "/{key}/{entity}")
            t.expand(key=key, entity=remote(entity)._id).delete()
        elif entity:
            t = ResourceTemplate(remote(self).uri.string + "/{entity}")
            t.expand(entity=remote(entity)._id).delete()
        else:
            raise TypeError("Illegal parameter combination for index removal")

    def query(self, query):
        """ Query the index according to the supplied query criteria, returning
        a list of matched entities.

        The query syntax used should be appropriate for the configuration of
        the index being queried. For indexes with default configuration, this
        should be Apache Lucene query syntax.
        """
        resource = self._query_template.expand(query=query)
        for result in resource.get().content:
            yield self.graph._hydrate(result)

    def _query_with_score(self, query, order):
        resource = self._query_template.expand(query=query, order=order)
        for result in resource.get().content:
            yield self.graph._hydrate(result), result["score"]

    def query_by_index(self, query):
        return self._query_with_score(query, "index")

    def query_by_relevance(self, query):
        return self._query_with_score(query, "relevance")

    def query_by_score(self, query):
        return self._query_with_score(query, "score")

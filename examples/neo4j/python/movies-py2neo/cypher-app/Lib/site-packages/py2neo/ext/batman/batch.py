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


import logging

from py2neo.compat import integer
from py2neo.database import GraphError, Resource
from py2neo.packages.httpstream.packages.urimagic import percent_encode
from py2neo.types import Node, Relationship, cast as core_cast, cast_node, cast_relationship, remote
from .jobs import Job, JobResult, Target, CreateNodeJob, CreateRelationshipJob, CreatePathJob, \
    CreateUniquePathJob, DeleteEntityJob, PushPropertyJob, PushPropertiesJob, DeletePropertyJob, \
    DeletePropertiesJob, AddNodeLabelsJob, RemoveNodeLabelJob, PushNodeLabelsJob
from .util import NodePointer


log = logging.getLogger("py2neo.ext.batch")


def cast(obj):
    if isinstance(obj, integer):
        obj = NodePointer(obj)
    elif isinstance(obj, tuple):
        obj = tuple(NodePointer(x) if isinstance(x, integer) else x for x in obj)
    return core_cast(obj)


def pendulate(collection):
    count = len(collection)
    for i in range(count):
        if i % 2 == 0:
            index = i // 2
        else:
            index = count - ((i + 1) // 2)
        yield index, collection[index]


class BatchFinished(GraphError):
    """ Raised when actions are attempted against a :class:`.Batch`
    that is no longer available for use.
    """

    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return "%s finished" % self.obj.__class__.__name__


class BatchRunner(object):
    """ Resource for batch execution.
    """

    def __init__(self, uri):
        self.resource = Resource(uri)

    def post(self, batch):
        num_jobs = len(batch)
        plural = "" if num_jobs == 1 else "s"
        log.info("> Sending batch request with %s job%s", num_jobs, plural)
        data = []
        for i, job in enumerate(batch):
            if job.finished:
                raise BatchFinished(job)
            else:
                job.finished = True
            log.info("> {%s} %s", i, job)
            data.append(dict(job, id=i))
        response = self.resource.post(data)
        log.info("< Received batch response for %s job%s", num_jobs, plural)
        return response

    def run(self, batch):
        """ Execute a collection of jobs and return all results.

        :param batch: A :class:`.Batch` of jobs.
        :rtype: :class:`list`
        """
        response = self.post(batch)
        try:
            results = []
            for result_data in response.content:
                result = JobResult.hydrate(result_data, batch)
                log.info("< %s", result)
                results.append(result)
            return results
        except ValueError:
            # Here, we're looking to gracefully handle a Neo4j server bug
            # whereby a response is received with no content and
            # 'Content-Type: application/json'. Given that correct JSON
            # technically needs to contain {} at minimum, the JSON
            # parser fails with a ValueError.
            if response.content_length == 0:
                from sys import exc_info
                from traceback import extract_tb
                type_, value, traceback = exc_info()
                for filename, line_number, function_name, text in extract_tb(traceback):
                    if "json" in filename and "decode" in function_name:
                        return []
            raise
        finally:
            response.close()


class Batch(object):
    """ A collection of :class:`.Job` objects that can be submitted
    to a :class:`.BatchRunner`. References to previous jobs are only
    valid **within the same batch** and will not work across batches.
    """

    #: The graph with which this batch is associated
    graph = None

    def __init__(self, graph):
        self.graph = graph
        self.runner = BatchRunner(remote(self.graph).metadata["batch"])
        self.jobs = []

    def __getitem__(self, index):
        return self.jobs[index]

    def __len__(self):
        return len(self.jobs)

    def __bool__(self):
        return bool(self.jobs)

    def __nonzero__(self):
        return bool(self.jobs)

    def __iter__(self):
        return iter(self.jobs)

    def resolve(self, node):
        """ Convert any references to previous jobs within the same batch
        into NodePointer objects.
        """
        if isinstance(node, Job):
            return NodePointer(self.find(node))
        else:
            return node

    def append(self, job):
        """ Add a job to this batch.

        :param job: A :class:`.Job` object to add to this batch.
        :rtype: :class:`.Job`
        """
        self.jobs.append(job)
        return job

    def find(self, job):
        """ Find the position of a job within this batch.
        """
        for i, candidate_job in pendulate(self.jobs):
            if candidate_job == job:
                return i
        raise ValueError("Job not found in batch")


class ReadBatch(Batch):
    """ Generic batch execution facility for data read requests,
    """

    def __init__(self, graph):
        Batch.__init__(self, graph)

    def run(self):
        return [result.content for result in self.graph.batch.run(self)]


class WriteBatch(Batch):
    """ Generic batch execution facility for data write requests. Most methods
    return a :class:`.BatchRequest` object that can be used as a reference
    in other methods. See the :meth:`.WriteBatch.create` method for an example
    of this.
    """

    def __init__(self, graph):
        Batch.__init__(self, graph)

    def run(self):
        return [result.content for result in self.runner.run(self)]

    def create(self, abstract):
        """ Create a node or relationship based on the abstract entity
        provided.

        :param abstract: node or relationship
        :return: :class:`.Job`
        """
        entity = cast(abstract)
        if isinstance(entity, Node):
            return self.append(CreateNodeJob(**entity))
        elif isinstance(entity, Relationship):
            start_node = self.resolve(entity.start_node())
            end_node = self.resolve(entity.end_node())
            return self.append(CreateRelationshipJob(start_node, entity.type(), end_node, **entity))
        else:
            raise TypeError(entity)

    def create_path(self, node, *rels_and_nodes):
        """ Construct a path across a specified set of nodes and relationships.
        Nodes may be existing concrete node instances, abstract nodes or
        :py:const:`None` but references to other requests are not supported.

        :param node: start node
        :param rels_and_nodes: alternating relationships and nodes
        :return: :class:`.Job`
        """
        return self.append(CreatePathJob(self.graph, node, *rels_and_nodes))

    def get_or_create_path(self, node, *rels_and_nodes):
        """ Construct a unique path across a specified set of nodes and
        relationships, adding only parts that are missing. Nodes may be
        existing concrete node instances, abstract nodes or :py:const:`None`
        but references to other requests are not supported.

        :param node: start node
        :param rels_and_nodes: alternating relationships and nodes
        :return: :class:`.Job`
        """
        return self.append(CreateUniquePathJob(self.graph, node, *rels_and_nodes))

    def delete(self, entity):
        """ Delete a node or relationship from the graph.

        :param entity: node or relationship to delete
        :return: :class:`.Job`
        """
        return self.append(DeleteEntityJob(self.resolve(entity)))

    def set_property(self, entity, key, value):
        """ Set a single property on a node or relationship.

        :param entity: node or relationship on which to set property
        :param key: property key
        :param value: property value
        :return: :class:`.Job`
        """
        return self.append(PushPropertyJob(self.resolve(entity), key, value))

    def set_properties(self, entity, properties):
        """ Replace all properties on a node or relationship.

        :param entity: node or relationship on which to set properties
        :param properties: properties
        :return: :class:`.Job`
        """
        return self.append(PushPropertiesJob(self.resolve(entity), properties))

    def delete_property(self, entity, key):
        """ Delete a single property from a node or relationship.

        :param entity: node or relationship from which to delete property
        :param key: property key
        :return: :class:`.Job`
        """
        return self.append(DeletePropertyJob(self.resolve(entity), key))

    def delete_properties(self, entity):
        """ Delete all properties from a node or relationship.

        :param entity: node or relationship from which to delete properties
        :return: :class:`.Job`
        """
        return self.append(DeletePropertiesJob(self.resolve(entity)))

    def add_labels(self, node, *labels):
        """ Add labels to a node.

        :param node: node to which to add labels
        :param labels: text labels
        :return: :class:`.Job`
        """
        return self.append(AddNodeLabelsJob(self.resolve(node), *labels))

    def remove_label(self, node, label):
        """ Remove a label from a node.

        :param node: node from which to remove labels (can be a reference to
            another request within the same batch)
        :param label: text label
        :return: :class:`.Job`
        """
        return self.append(RemoveNodeLabelJob(self.resolve(node), label))

    def set_labels(self, node, *labels):
        """ Replace all labels on a node.

        :param node: node on which to replace labels (can be a reference to
            another request within the same batch)
        :param labels: text labels
        :return: :class:`.Job`
        """
        return self.append(PushNodeLabelsJob(self.resolve(node), labels))


class ManualIndexReadBatch(ReadBatch):
    """ Generic batch execution facility for data read requests,
    """

    def append_get(self, uri):
        return self.append(Job("GET", Target(uri)))

    def _index(self, content_type, index):
        """ Fetch an Index object.
        """
        from py2neo.ext.batman import ManualIndexManager, ManualIndex
        if isinstance(index, ManualIndex):
            if content_type == index._content_type:
                return index
            else:
                raise TypeError("Index is not for {0}s".format(content_type))
        else:
            return ManualIndexManager(self.graph).get_or_create_index(content_type, str(index))

    def get_indexed_nodes(self, index, key, value):
        """ Fetch all nodes indexed under a given key-value pair.

        :param index: index name or instance
        :param key: key under which nodes are indexed
        :param value: value under which nodes are indexed
        :return: :class:`.Job`
        """
        index = self._index(Node, index)
        uri = index._searcher_stem_for_key(key) + percent_encode(value)
        return self.append_get(uri)


class ManualIndexWriteBatch(WriteBatch):
    """ Generic batch execution facility for data write requests. Most methods
    return a :class:`.BatchRequest` object that can be used as a reference in
    other methods.
    """

    def append_post(self, uri, body=None):
        return self.append(Job("POST", Target(uri), body))

    def append_delete(self, uri):
        return self.append(Job("DELETE", Target(uri)))

    def _uri_for(self, resource, *segments, **kwargs):
        """ Return a relative URI in string format for the entity specified
        plus extra path segments.
        """
        if isinstance(resource, int):
            uri = "{{{0}}}".format(resource)
        elif isinstance(resource, NodePointer):
            uri = "{{{0}}}".format(resource.address)
        elif isinstance(resource, Job):
            uri = "{{{0}}}".format(self.find(resource))
        else:
            remote_resource = remote(resource)
            remote_graph = remote(remote_resource.graph)
            graph_uri = remote_graph.uri.string
            entity_uri = remote_resource.uri.string
            uri = entity_uri[len(graph_uri):]
        if segments:
            if not uri.endswith("/"):
                uri += "/"
            uri += "/".join(map(percent_encode, segments))
        query = kwargs.get("query")
        if query is not None:
            uri += "?" + query
        return uri

    def _index(self, content_type, index):
        """ Fetch an Index object.
        """
        from py2neo.ext.batman import ManualIndexManager, ManualIndex
        if isinstance(index, ManualIndex):
            if content_type == index._content_type:
                return index
            else:
                raise TypeError("Index is not for {0}s".format(content_type))
        else:
            return ManualIndexManager(self.graph).get_or_create_index(content_type, str(index))

    def __init__(self, graph):
        super(ManualIndexWriteBatch, self).__init__(graph)
        self.__new_uniqueness_modes = None

    ### ADD TO INDEX ###

    def _add_to_index(self, cls, index, key, value, entity, query=None):
        uri = self._uri_for(self._index(cls, index), query=query)
        return self.append_post(uri, {
            "key": key,
            "value": value,
            "uri": self._uri_for(entity),
        })

    def add_to_index(self, cls, index, key, value, entity):
        """ Add an existing node or relationship to an index.

        :param cls: the type of indexed entity
        :param index: index or index name
        :param key: index entry key
        :param value: index entry value
        :param entity: node or relationship to add to the index
        :return: :class:`.Job`
        """
        return self._add_to_index(cls, index, key, value, entity)

    def add_to_index_or_fail(self, cls, index, key, value, entity):
        """ Add an existing node or relationship uniquely to an index, failing
        the entire batch if such an entry already exists.

        .. warning::
            Uniqueness modes for legacy indexes have been broken in recent
            server versions and therefore this method may not work as expected.

        :param cls: the type of indexed entity
        :param index: index or index name
        :param key: index entry key
        :param value: index entry value
        :param entity: node or relationship to add to the index
        :return: :class:`.Job`
        """
        query = "uniqueness=create_or_fail"
        return self._add_to_index(cls, index, key, value, entity, query)

    def get_or_add_to_index(self, cls, index, key, value, entity):
        """ Fetch a uniquely indexed node or relationship if one exists,
        otherwise add an existing entity to the index.

        :param cls: the type of indexed entity
        :param index: index or index name
        :param key: index entry key
        :param value: index entry value
        :param entity: node or relationship to add to the index
        :return: :class:`.Job`
        """
        query = "uniqueness=get_or_create"
        return self._add_to_index(cls, index, key, value, entity, query)

    ### CREATE IN INDEX ###

    def _create_in_index(self, cls, index, key, value, abstract, query=None):
        uri = self._uri_for(self._index(cls, index), query=query)
        if cls is Node:
            a = cast_node(abstract)
            return self.append_post(uri, {
                "key": key,
                "value": value,
                "properties": dict(a),
            })
        elif cls is Relationship:
            r = cast_relationship(abstract)
            return self.append_post(uri, {
                "key": key,
                "value": value,
                "start": self._uri_for(abstract.start_node()),
                "type": str(abstract.type()),
                "end": self._uri_for(abstract.end_node()),
                "properties": dict(r),
            })
        else:
            raise TypeError(cls)

    # Removed create_in_index as parameter combination not supported by server

    def create_in_index_or_fail(self, cls, index, key, value, abstract=None):
        """ Create a new node or relationship and add it uniquely to an index,
        failing the entire batch if such an entry already exists.

        .. warning::
            Uniqueness modes for legacy indexes have been broken in recent
            server versions and therefore this method may not work as expected.

        :param cls: the type of indexed entity
        :param index: index or index name
        :param key: index entry key
        :param value: index entry value
        :param abstract: abstract node or relationship to create
        :return: :class:`.Job`
        """
        query = "uniqueness=create_or_fail"
        return self._create_in_index(cls, index, key, value, abstract, query)

    def get_or_create_in_index(self, cls, index, key, value, abstract=None):
        """ Fetch a uniquely indexed node or relationship if one exists,
        otherwise create a new entity and add that to the index.

        :param cls: the type of indexed entity
        :param index: index or index name
        :param key: index entry key
        :param value: index entry value
        :param abstract: abstract node or relationship to create
        :return: :class:`.Job`
        """
        query = "uniqueness=get_or_create"
        if cls is Node:
            return self._create_in_index(cls, index, key, value, cast_node(abstract), query)
        elif cls is Relationship:
            return self._create_in_index(cls, index, key, value, cast_relationship(abstract), query)
        else:
            raise TypeError("Unindexable class")

    ### REMOVE FROM INDEX ###

    def remove_from_index(self, cls, index, key=None, value=None, entity=None):
        """ Remove any nodes or relationships from an index that match a
        particular set of criteria. Allowed parameter combinations are:

        `key`, `value`, `entity`
            remove a specific node or relationship indexed under a given
            key-value pair

        `key`, `entity`
            remove a specific node or relationship indexed against a given key
            and with any value

        `entity`
            remove all occurrences of a specific node or relationship
            regardless of key or value

        :param cls: the type of indexed entity
        :param index: index or index name
        :param key: index entry key
        :param value: index entry value
        :param entity: node or relationship to remove from the index
        :return: :class:`.Job`
        """
        index = self._index(cls, index)
        if key and value and entity:
            uri = self._uri_for(index, key, value, remote(entity)._id)
        elif key and entity:
            uri = self._uri_for(index, key, remote(entity)._id)
        elif entity:
            uri = self._uri_for(index, remote(entity)._id)
        else:
            raise TypeError("Illegal parameter combination for index removal")
        return self.append_delete(uri)

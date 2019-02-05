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


import json

from py2neo.compat import ustr
from py2neo.database import Graph, Cursor, cypher_request
from py2neo.database.status import GraphError
from py2neo.packages.httpstream.packages.urimagic import percent_encode, URI
from py2neo.types import Path, Relatable, remote
from py2neo.util import raise_from
from .util import NodePointer, BatchError


def _create_query(p, unique=False):
    initial_match_clause = []
    path, values, params = [], [], {}

    def append_node(i, node):
        remote_node = remote(node)
        if node is None:
            path.append("(n{0})".format(i))
            values.append("n{0}".format(i))
        elif remote_node:
            path.append("(n{0})".format(i))
            initial_match_clause.append("MATCH (n{0}) WHERE id(n{0})={{i{0}}}".format(i))
            params["i{0}".format(i)] = remote_node._id
            values.append("n{0}".format(i))
        else:
            path.append("(n{0} {{p{0}}})".format(i))
            params["p{0}".format(i)] = dict(node)
            values.append("n{0}".format(i))

    def append_relationship(i, relationship):
        if relationship:
            path.append("-[r{0}:`{1}` {{q{0}}}]->".format(i, relationship.type()))
            params["q{0}".format(i)] = dict(relationship)
            values.append("r{0}".format(i))
        else:
            path.append("-[r{0}:`{1}`]->".format(i, relationship.type()))
            values.append("r{0}".format(i))

    nodes = p.nodes()
    append_node(0, nodes[0])
    for i, relationship in enumerate(p.relationships()):
        append_relationship(i, relationship)
        append_node(i + 1, nodes[i + 1])
    clauses = list(initial_match_clause)
    if unique:
        clauses.append("CREATE UNIQUE p={0}".format("".join(path)))
    else:
        clauses.append("CREATE p={0}".format("".join(path)))
    clauses.append("RETURN p")
    query = "\n".join(clauses)
    return query, params


class Target(object):
    """ A callable target for a batch job. This may refer directly to a URI
    or to an object that can be resolved to a URI, such as a :class:`py2neo.Node`.
    """

    #: The entity behind this target.
    entity = None

    #: Additional path segments to append to the resolved URI.
    segments = None

    def __init__(self, entity, *segments):
        self.entity = entity
        self.segments = segments

    @property
    def uri_string(self):
        """ The fully resolved URI string for this target.

        :rtype: string

        """
        if isinstance(self.entity, int):
            uri_string = "{%d}" % self.entity
        elif isinstance(self.entity, NodePointer):
            uri_string = "{%d}" % self.entity.address
        else:
            remote_entity = remote(self.entity)
            if remote_entity:
                uri_string = remote_entity.ref
            else:
                uri_string = ustr(self.entity)
        if self.segments:
            if not uri_string.endswith("/"):
                uri_string += "/"
            uri_string += "/".join(map(percent_encode, self.segments))
        return uri_string


class Job(Relatable):
    """ A single request for inclusion within a :class:`.Batch`.
    """

    #: The graph for which this job is intended (optional).
    graph = None

    #: Indicates whether or not the result should be
    #: interpreted as raw data.
    raw_result = False

    #: The HTTP method for the request.
    method = None

    #: A :class:`.Target` object used to determine the destination URI.
    target = None

    #: The request payload.
    body = None

    #: Indicates whether the job has been submitted.
    finished = False

    def __init__(self, method, target, body=None):
        self.method = method
        self.target = target
        self.body = body

    def __repr__(self):
        parts = [self.method, self.target.uri_string]
        if self.body is not None:
            parts.append(json.dumps(self.body, separators=",:"))
        return " ".join(parts)

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(id(self))

    def __iter__(self):
        yield "method", self.method
        yield "to", self.target.uri_string
        if self.body is not None:
            yield "body", self.body


class JobResult(object):
    """ The result returned from the server for a single
    :class:`.Job` following a :class:`.Batch` submission.
    """

    @classmethod
    def hydrate(cls, data, batch):
        graph = getattr(batch, "graph", None)
        job_id = data["id"]
        uri = data["from"]
        status_code = data.get("status")
        location = data.get("location")
        if graph is None or batch[job_id].raw_result:
            body = data.get("body")
        else:
            body = None
            try:
                body = graph._hydrate(data.get("body"))
            except GraphError as error:
                message = "Batch job %s failed with %s\n%s" % (
                    job_id, error.__class__.__name__, ustr(error))
                raise_from(BatchError(message, batch, job_id, status_code, uri, location), error)
            else:
                # If Cypher results, reduce to single row or single value if possible
                if isinstance(body, Cursor):
                    if body.forward():
                        record = body.current()
                        width = len(record)
                        if width == 1:
                            body = record[0]
                        else:
                            body = record
                    else:
                        body = None
        return cls(batch, job_id, uri, status_code, location, body)

    #: The :class:`.Batch` from which this result was returned.
    batch = None

    #: The unique ID for this job within the batch.
    job_id = None

    #: The URI destination of the original job.
    uri = None

    #: The status code returned for this job.
    status_code = None

    #: The ``Location`` header returned for this job (if included).
    location = None

    #: The response content for this job.
    content = None

    def __init__(self, batch, job_id, uri, status_code=None, location=None, content=None):
        self.batch = batch
        self.job_id = job_id
        self.uri = URI(uri)
        self.status_code = status_code or 200
        self.location = URI(location)
        self.content = content

    def __repr__(self):
        parts = ["{" + ustr(self.job_id) + "}", ustr(self.status_code)]
        if self.content is not None:
            parts.append(repr(self.content))
        return " ".join(parts)

    @property
    def graph(self):
        """ The corresponding graph for this result.

        :rtype: :class:`py2neo.Graph`

        """
        return self.batch.graph

    @property
    def job(self):
        """ The original job behind this result.

        :rtype: :class:`.Job`

        """
        return self.batch[self.job_id]


class CypherJob(Job):

    target = Target("transaction/commit")

    def __init__(self, statement, parameters=None):
        Job.__init__(self, "POST", self.target,
                     {"statements": [cypher_request(statement, parameters)]})


class PullPropertiesJob(Job):

    raw_result = True

    def __init__(self, entity):
        Job.__init__(self, "GET", Target(entity, "properties"))


class PullNodeLabelsJob(Job):

    raw_result = True

    def __init__(self, node):
        Job.__init__(self, "GET", Target(node, "labels"))


class PullRelationshipJob(Job):

    raw_result = True

    def __init__(self, relationship):
        Job.__init__(self, "GET", Target(relationship))


class PushPropertyJob(Job):

    def __init__(self, entity, key, value):
        Job.__init__(self, "PUT", Target(entity, "properties", key), value)


class PushPropertiesJob(Job):

    def __init__(self, entity, properties):
        Job.__init__(self, "PUT", Target(entity, "properties"), dict(properties))


class PushNodeLabelsJob(Job):

    def __init__(self, node, labels):
        Job.__init__(self, "PUT", Target(node, "labels"), set(labels))


class CreateNodeJob(Job):

    target = Target("node")

    def __init__(self, **properties):
        Job.__init__(self, "POST", self.target, properties)


class CreateRelationshipJob(Job):

    def __init__(self, start_node, type, end_node, **properties):
        body = {"type": type, "to": Target(end_node).uri_string}
        if properties:
            body["data"] = properties
        Job.__init__(self, "POST", Target(start_node, "relationships"), body)


class CreatePathJob(CypherJob):

    def __init__(self, *entities):
        # Fudge to allow graph to be passed in so Cypher syntax
        # detection can occur. Can be removed when only 2.0+ is
        # supported.
        if isinstance(entities[0], Graph):
            self.graph, entities = entities[0], entities[1:]
        path = Path(*(entity or {} for entity in entities))
        CypherJob.__init__(self, *_create_query(path))


class CreateUniquePathJob(CypherJob):

    def __init__(self, *entities):
        # Fudge to allow graph to be passed in so Cypher syntax
        # detection can occur. Can be removed when only 2.0+ is
        # supported.
        if isinstance(entities[0], Graph):
            self.graph, entities = entities[0], entities[1:]
        path = Path(*(entity or {} for entity in entities))
        CypherJob.__init__(self, *_create_query(path, unique=True))


class DeleteEntityJob(Job):

    def __init__(self, entity):
        Job.__init__(self, "DELETE", Target(entity))


class DeletePropertyJob(Job):

    def __init__(self, entity, key):
        Job.__init__(self, "DELETE", Target(entity, "properties", key))


class DeletePropertiesJob(Job):

    def __init__(self, entity):
        Job.__init__(self, "DELETE", Target(entity, "properties"))


class AddNodeLabelsJob(Job):

    def __init__(self, node, *labels):
        Job.__init__(self, "POST", Target(node, "labels"), set(labels))


class RemoveNodeLabelJob(Job):

    def __init__(self, entity, label):
        Job.__init__(self, "DELETE", Target(entity, "labels", label))

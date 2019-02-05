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


from io import StringIO
from json import dumps as json_dumps
from sys import stdout

from py2neo.compat import ustr
from py2neo.types import Node, Relationship, Path
from py2neo.util import is_collection


class CypherWriter(object):
    """ Writer for Cypher data. This can be used to write to any
    file-like object, such as standard output.
    """

    safe_first_chars = u"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
    safe_chars = u"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"

    default_sequence_separator = u","
    default_key_value_separator = u":"

    def __init__(self, file=None, **kwargs):
        self.file = file or stdout
        self.sequence_separator = kwargs.get("sequence_separator", self.default_sequence_separator)
        self.key_value_separator = \
            kwargs.get("key_value_separator", self.default_key_value_separator)

    def write(self, obj):
        """ Write any entity, value or collection.

        :arg obj:
        """
        if obj is None:
            pass
        elif isinstance(obj, Node):
            self.write_node(obj)
        elif isinstance(obj, Relationship):
            self.write_relationship(obj)
        elif isinstance(obj, Path):
            self.write_walkable(obj)
        elif isinstance(obj, dict):
            self.write_map(obj)
        elif is_collection(obj):
            self.write_list(obj)
        else:
            self.write_value(obj)

    def write_value(self, value):
        """ Write a value.

        :arg value:
        """
        self.file.write(ustr(json_dumps(value, ensure_ascii=False)))

    def write_identifier(self, identifier):
        """ Write an identifier.

        :arg identifier:
        """
        if not identifier:
            raise ValueError("Invalid identifier")
        identifier = ustr(identifier)
        safe = (identifier[0] in self.safe_first_chars and
                all(ch in self.safe_chars for ch in identifier[1:]))
        if not safe:
            self.file.write(u"`")
            self.file.write(identifier.replace(u"`", u"``"))
            self.file.write(u"`")
        else:
            self.file.write(identifier)

    def write_list(self, collection):
        """ Write a list.

        :arg collection:
        """
        self.file.write(u"[")
        link = u""
        for value in collection:
            self.file.write(link)
            self.write(value)
            link = self.sequence_separator
        self.file.write(u"]")

    def write_literal(self, text):
        """ Write literal text.

        :arg text:
        """
        self.file.write(ustr(text))

    def write_map(self, mapping, private=False):
        """ Write a map.

        :arg mapping:
        :arg private:
        """
        self.file.write(u"{")
        link = u""
        for key, value in sorted(dict(mapping).items()):
            if key.startswith("_") and not private:
                continue
            self.file.write(link)
            self.write_identifier(key)
            self.file.write(self.key_value_separator)
            self.write(value)
            link = self.sequence_separator
        self.file.write(u"}")

    def write_node(self, node, name=None, full=True):
        """ Write a node.

        :arg node:
        :arg name:
        :arg full:
        """
        self.file.write(u"(")
        if name is None:
            name = node.__name__
        self.write_identifier(name)
        if full:
            for label in sorted(node.labels()):
                self.write_literal(u":")
                self.write_identifier(label)
            if node:
                self.file.write(u" ")
                self.write_map(dict(node))
        self.file.write(u")")

    def write_relationship(self, relationship, name=None):
        """ Write a relationship (including nodes).

        :arg relationship:
        :arg name:
        """
        self.write_node(relationship.start_node(), full=False)
        self.file.write(u"-")
        self.write_relationship_detail(relationship, name)
        self.file.write(u"->")
        self.write_node(relationship.end_node(), full=False)

    def write_relationship_detail(self, relationship, name=None):
        """ Write a relationship (excluding nodes).

        :arg relationship:
        :arg name:
        """
        self.file.write(u"[")
        if name is not None:
            self.write_identifier(name)
        if type:
            self.file.write(u":")
            self.write_identifier(relationship.type())
        if relationship:
            self.file.write(u" ")
            self.write_map(relationship)
        self.file.write(u"]")

    def write_subgraph(self, subgraph):
        """ Write a subgraph.

        :arg subgraph:
        """
        self.write_literal("({")
        for i, node in enumerate(subgraph.nodes()):
            if i > 0:
                self.write_literal(", ")
            self.write_node(node)
        self.write_literal("}, {")
        for i, relationship in enumerate(subgraph.relationships()):
            if i > 0:
                self.write_literal(", ")
            self.write_relationship(relationship)
        self.write_literal("})")

    def write_walkable(self, walkable):
        """ Write a walkable.

        :arg walkable:
        """
        nodes = walkable.nodes()
        for i, relationship in enumerate(walkable):
            node = nodes[i]
            self.write_node(node, full=False)
            forward = relationship.start_node() == node
            self.file.write(u"-" if forward else u"<-")
            self.write_relationship_detail(relationship)
            self.file.write(u"->" if forward else u"-")
        self.write_node(nodes[-1], full=False)


def cypher_escape(identifier):
    """ Escape a Cypher identifier in backticks.

    ::

        >>> cypher_escape("this is a `label`")
        '`this is a ``label```'

    :arg identifier:
    """
    s = StringIO()
    writer = CypherWriter(s)
    writer.write_identifier(identifier)
    return s.getvalue()


def cypher_repr(obj):
    """ Generate the Cypher representation of an object.

    :arg obj:
    """
    s = StringIO()
    writer = CypherWriter(s)
    writer.write(obj)
    return s.getvalue()

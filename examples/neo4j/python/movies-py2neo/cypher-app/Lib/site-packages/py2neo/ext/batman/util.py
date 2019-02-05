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


from py2neo.compat import xstr
from py2neo.database.status import GraphError
from py2neo.types import Relatable


class NodePointer(Relatable):
    """ Pointer to a :class:`Node` object. This can be used in a batch
    context to point to a node not yet created.
    """

    #: The address or index to which this pointer points.
    address = None

    def __init__(self, address):
        self.address = address

    def __repr__(self):
        return "<NodePointer address=%s>" % self.address

    def __str__(self):
        return xstr(self.__unicode__())

    def __unicode__(self):
        return "{%s}" % self.address

    def __eq__(self, other):
        return self.address == other.address

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.address)


class BatchError(GraphError):
    """ Wraps a base :class:`py2neo.GraphError` within a batch context.
    """

    batch = None
    job_id = None
    status_code = None
    uri = None
    location = None

    def __init__(self, message, batch, job_id, status_code, uri, location=None, **kwargs):
        GraphError.__init__(self, message, **kwargs)
        self.batch = batch
        self.job_id = job_id
        self.status_code = status_code
        self.uri = uri
        self.location = location

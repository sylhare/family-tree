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


from base64 import b64encode
from os import getenv
from py2neo.packages.httpstream.packages.urimagic import URI
from py2neo.packages.neo4j.v1 import basic_auth


#: Authentication dictionary mapping server addresses to auth details
keyring = {}


class ServerAddress(object):
    """ A DBMS or graph database address.
    """

    def __init__(self, *uris, **settings):
        self.__settings = {}

        def apply_uri(u):
            uri_object = URI(u)
            if uri_object.scheme == "bolt":
                self.__settings.setdefault("bolt_port", 7687)
            if uri_object.scheme == "https":
                self.__settings["secure"] = True
            if uri_object.host:
                self.__settings["host"] = uri_object.host
            if uri_object.port:
                self.__settings["%s_port" % uri_object.scheme] = uri_object.port

        # Apply URIs
        for uri in uris:
            apply_uri(uri)

        # Apply individual settings
        self.__settings.update({k: v for k, v in settings.items()
                                if k in ["bolt", "secure", "host",
                                         "http_port", "https_port", "bolt_port"]})

    def __repr__(self):
        return "<ServerAddress settings=%r>" % self.__settings

    def __getitem__(self, item):
        return self.__settings[item]

    def __eq__(self, other):
        return (self.bolt is None or other.bolt is None or self.bolt == other.bolt) and \
                self.secure == other.secure and self.host == other.host and \
                self.http_port == other.http_port and self.https_port == other.https_port

    def __hash__(self):
        return hash((self.bolt, self.secure, self.host, self.http_port, self.https_port))

    def keys(self):
        return self.__settings.keys()

    @property
    def bolt(self):
        return self.__settings.get("bolt", None)  # default=autodetect

    @property
    def secure(self):
        return self.__settings.get("secure", False)

    @property
    def host(self):
        return self.__settings.get("host", "localhost")

    @property
    def http_port(self):
        return self.__settings.get("http_port", 7474)

    @property
    def https_port(self):
        return self.__settings.get("https_port", 7473)

    @property
    def bolt_port(self):
        return self.__settings.get("bolt_port", 7687)

    def bolt_uri(self, path):
        return "bolt://%s:%d%s" % (self.host, self.bolt_port, path)

    def http_uri(self, path):
        if self.secure:
            return "https://%s:%d%s" % (self.host, self.https_port, path)
        else:
            return "http://%s:%d%s" % (self.host, self.http_port, path)


class ServerAuth(object):

    def __init__(self, *uris, **settings):
        self.__settings = {
            "user": "neo4j",
        }

        def apply_uri(u):
            uri_object = URI(u)
            if uri_object.user_info:
                apply_auth(uri_object.user_info)

        def apply_auth(a):
            user, _, password = a.partition(":")
            if user:
                self.__settings["user"] = user
            if password:
                self.__settings["password"] = password

        # Apply URIs
        for uri in uris:
            apply_uri(uri)

        # Apply individual settings
        self.__settings.update({k: v for k, v in settings.items()
                                if k in ["user", "password"]})

        if self.password is None:
            raise TypeError("No auth details available")

    def __repr__(self):
        return "<ServerAuth settings=%r>" % self.__settings

    @property
    def user(self):
        return self.__settings.get("user")

    @property
    def password(self):
        return self.__settings.get("password")

    @property
    def bolt_auth_token(self):
        return basic_auth(self.user, self.password)

    @property
    def http_authorization(self):
        return 'Basic ' + b64encode((self.user + ":" +
                                     self.password).encode("UTF-8")).decode("ASCII")


def register_server(*uris, **settings):
    """ Register server address details and return a
    :class:`.ServerAddress` instance.

    :param uris:
    :param settings:
    :return:
    """
    new_address = ServerAddress(*uris, **settings)
    try:
        new_auth = ServerAuth(*uris, **settings)
    except TypeError:
        new_auth = None
    if new_auth is None:
        keyring.setdefault(new_address)
    else:
        keyring[new_address] = new_auth
    return new_address


def _register_server_from_environment():
    neo4j_uri = getenv("NEO4J_URI")
    if neo4j_uri:
        settings = {}
        neo4j_auth = getenv("NEO4J_AUTH")
        if neo4j_auth:
            user, _, password = neo4j_auth.partition(":")
            settings["user"] = user
            settings["password"] = password
        register_server(neo4j_uri, **settings)


def get_auth(address):
    for addr, auth in keyring.items():
        if addr == address:
            return auth
    raise KeyError(address)


def authenticate(host_port, user, password):
    """ Set HTTP basic authentication values for specified `host_port` for use
    with both Neo4j 2.2 built-in authentication as well as if a database server
    is behind (for example) an Apache proxy. The code below shows a simple example::

        from py2neo import authenticate, Graph

        # set up authentication parameters
        authenticate("camelot:7474", "arthur", "excalibur")

        # connect to authenticated graph database
        graph = Graph("http://camelot:7474/db/data/")

    Note: a `host_port` can be either a server name or a server name and port
    number but must match exactly that used within the Graph
    URI.

    :arg host_port: the host and optional port requiring authentication
        (e.g. "bigserver", "camelot:7474")
    :arg user: the user name to authenticate as
    :arg password: the password
    """
    register_server("http://%s/" % host_port, user=user, password=password)


_register_server_from_environment()

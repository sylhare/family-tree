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


"""
********************************************
``neokit`` -- Command Line Toolkit for Neo4j
********************************************

Neokit is a standalone module for managing one or more Neo4j server
installations. The Neokit classes may be used programmatically but
will generally be invoked via the command line interface. If Neokit
has been installed as part of the Py2neo package, the command line
tool will be available as `neokit`; otherwise, it can be called
as a Python module: `python -m neokit`.


Command Line Usage
==================

Installing a Neo4j archive
--------------------------
::

    $ neokit install 3.0


API
===
"""


from argparse import ArgumentParser
from base64 import b64encode
from contextlib import contextmanager
from json import dumps as json_dumps
from os import chdir, curdir, getenv, linesep, listdir, makedirs, rename
from os.path import basename, exists as path_exists, expanduser, isdir, isfile, join as path_join, abspath
import re
from shutil import rmtree
from socket import create_connection
from subprocess import call, check_call, check_output, CalledProcessError
from sys import argv, stdout, stderr
from tarfile import TarFile, ReadError
from textwrap import dedent
from time import sleep
try:
    from urllib.request import Request, urlopen, urlretrieve, HTTPError
except ImportError:
    from urllib import urlretrieve
    from urllib2 import Request, urlopen, HTTPError

try:
    from configparser import SafeConfigParser

    class PropertiesParser(SafeConfigParser):

        def read_properties(self, filename, section=None):
            if not section:
                b = basename(filename)
                if b.endswith(".properties"):
                    section = b[:-11]
                else:
                    section = b
            with open(filename) as f:
                data = f.read()
            self.read_string("[%s]\n%s" % (section, data), filename)

except ImportError:
    from ConfigParser import SafeConfigParser
    from io import StringIO
    from codecs import open as codecs_open
    from os import SEEK_SET

    class PropertiesParser(SafeConfigParser):

        def read_properties(self, filename, section=None):
            if not section:
                b = basename(filename)
                if b.endswith(".properties"):
                    section = b[:-11]
                else:
                    section = b
            data = StringIO()
            data.write("[%s]\n" % section)
            with codecs_open(filename, encoding="utf-8") as f:
                data.write(f.read())
            data.seek(0, SEEK_SET)
            self.readfp(data)


SERVER_AUTH_FAILURE = 9
SERVER_NOT_RUNNING = 10
SERVER_ALREADY_RUNNING = 11

number_in_brackets = re.compile("\[(\d+)\]")

editions = [
    "community",
    "enterprise",
]
versions = [
    "2.0.0", "2.0.1", "2.0.2", "2.0.3", "2.0.4",
    "2.1.2", "2.1.3", "2.1.4", "2.1.5", "2.1.6", "2.1.7", "2.1.8",
    "2.2.0", "2.2.1", "2.2.2", "2.2.3", "2.2.4", "2.2.5", "2.2.6", "2.2.7", "2.2.8",
    "2.3.0", "2.3.1", "2.3.2",
    "3.0.0", "3.0.1-NIGHTLY",
]
version_aliases = {
    "2.0": "2.0.4",
    "2.0-LATEST": "2.0.4",
    "2.1": "2.1.8",
    "2.1-LATEST": "2.1.8",
    "2.2": "2.2.8",
    "2.2-LATEST": "2.2.8",
    "2.3": "2.3.2",
    "2.3-LATEST": "2.3.2",
    "3.0": "3.0.0",
    "3.0-MILESTONE": "3.0.0",
    "3.0-LATEST": "3.0.0",
    "3.0-SNAPSHOT": "3.0.1-NIGHTLY",
    "LATEST": "3.0.0",
    "MILESTONE": "3.0.0",
    "SNAPSHOT": "3.0.1-NIGHTLY",
}

dist = "http://dist.neo4j.org"
dist_overrides = {
    "3.0.0-NIGHTLY": "http://alpha.neohq.net/dist",
}


@contextmanager
def move_file(file_name):
    temp_file_name = file_name + ".backup"
    try:
        rename(file_name, temp_file_name)
    except OSError:
        renamed = False
    else:
        renamed = True
    yield temp_file_name
    if renamed:
        rename(temp_file_name, file_name)


class Unauthorized(Exception):
    """ Raised when auth fails.
    """


class Package(object):
    """ Represents a Neo4j archive.
    """

    def __init__(self, edition=None, version=None):
        edition = edition.lower() if edition else "community"
        if edition in editions:
            self.edition = edition
        else:
            raise ValueError("Unknown edition %r" % edition)
        version = version.upper() if version else "LATEST"
        self.snapshot = "SNAPSHOT" in version
        if version in version_aliases:
            version = version_aliases[version]
        if version in versions:
            self.version = version
        else:
            raise ValueError("Unknown version %r" % version)

    @property
    def key(self):
        """ The unique key that identifies the archive, e.g.
        ``community-2.3.2``.
        """
        return "%s-%s" % (self.edition, self.version)

    @property
    def name(self):
        """ The full name of the archive file, e.g.
        ``neo4j-community-2.3.2-unix.tar.gz``.
        """
        return "neo4j-%s-unix.tar.gz" % self.key

    @property
    def uri(self):
        """ The URI from which this archive may be downloaded, e.g.
        ``http://dist.neo4j.org/neo4j-community-2.3.2-unix.tar.gz``.
        """
        if self.version in dist_overrides:
            return "%s/%s" % (dist_overrides[self.version], self.name)
        else:
            return "%s/%s" % (dist, self.name)

    def download(self, path=".", overwrite=False):
        """ Download a Neo4j distribution to the specified path.

        :param path:
        :param overwrite:
        :return: the name of the downloaded file
        """
        file_name = path_join(path, self.name)
        if overwrite:
            if path_exists(file_name) and not isfile(file_name):
                raise IOError("Cannot overwrite directory %r" % file_name)
        elif not self.snapshot and path_exists(file_name):
            return file_name
        try:
            makedirs(path)
        except OSError:
            pass
        urlretrieve(self.uri, file_name)
        return file_name


class Warehouse(object):
    """ A local storage area for Neo4j installations.
    """

    def __init__(self, home=None):
        self.home = home or getenv("NEOKIT_HOME") or expanduser("~/.neokit")
        self.dist = path_join(self.home, "dist")
        self.run = path_join(self.home, "run")

    def get(self, name):
        """ Obtain a Neo4j installation by name.

        :param name:
        :return:
        """
        container = path_join(self.run, name)
        for dir_name in listdir(container):
            dir_path = path_join(container, dir_name)
            if isdir(dir_path):
                return GraphServer(dir_path)
        raise IOError("Could not locate server directory")

    def install(self, name, edition=None, version=None):
        """ Install Neo4j.

        :param name:
        :param edition:
        :param version:
        :return:
        """
        container = path_join(self.run, name)
        rmtree(container, ignore_errors=True)
        makedirs(container)
        archive_file = Package(edition, version).download(self.dist)
        try:
            with TarFile.open(archive_file, "r:gz") as archive:
                archive.extractall(container)
        except ReadError:
            # The tarfile module sometimes has trouble with certain tar
            # files for unknown reasons. This workaround falls back to
            # command line.
            check_call(["tar", "x", "-C", container, "-f", archive_file])
        return self.get(name)

    def uninstall(self, name):
        """ Remove a Neo4j installation.

        :param name:
        :return:
        """
        container = path_join(self.run, name)
        rmtree(container)

    def directory(self):
        """ Fetch a dictionary of :class:`.GraphServer` objects, keyed
        by name, for all available Neo4j installations.
        """
        try:
            return {name: self.get(name) for name in listdir(self.run) if not name.startswith(".")}
        except OSError:
            return {}

    def rename(self, name, new_name):
        """ Rename a Neo4j installation.

        :param name:
        :param new_name:
        :return:
        """
        rename(path_join(self.run, name), path_join(self.run, new_name))


class GraphServer(object):
    """ A Neo4j server installation.
    """

    config_file = None  # overridden in subclasses
    default_http_port = 7474

    def __new__(cls, home=None):
        home = home or abspath(curdir)
        instance = super(GraphServer, cls).__new__(cls)
        # Here follows a dirty hack to find out which version of Neo4j we're running.
        # If you are of a nervous disposition, look away now.
        lib = path_join(home, "lib")
        kernel_jars = [f for f in listdir(lib)
                       if f.startswith("neo4j-kernel-") and f.endswith(".jar")]
        if kernel_jars:
            kernel_jar = kernel_jars[0]
            kernel_version = kernel_jar[13:-4]
            major_version = int(kernel_version.partition(".")[0])
            if major_version >= 3:
                instance.__class__ = GraphServerV3
            else:
                instance.__class__ = GraphServerV2
        else:
            # Kernel jar not found, assume 3.0+
            instance.__class__ = GraphServerV3
        return instance

    def __init__(self, home=None):
        self.home = home or abspath(curdir)

    def __repr__(self):
        return "<%s home=%r>" % (self.__class__.__name__, self.home)

    @property
    def control_script(self):
        """ The file name of the control script for this server installation.
        """
        return path_join(self.home, "bin", "neo4j")

    @property
    def store_path(self):
        """ The location of the graph database store on disk.
        """
        return NotImplemented

    def config(self, key, default=None):
        """ Retrieve the value of a configuration item.

        :param key:
        :param default:
        :return:
        """
        config_file_path = path_join(self.home, "conf", self.config_file)
        with open(config_file_path, "r") as f_in:
            for line in f_in:
                if line.startswith(key + "="):
                    return line.strip().partition("=")[-1]
        return default

    def set_config(self, key, value):
        """ Update a single configuration value.

        :param key:
        :param value:
        """
        self.update_config({key: value})

    def update_config(self, properties):
        """ Update multiple configuration values.

        :param properties:
        """
        config_file_path = path_join(self.home, "conf", self.config_file)
        with open(config_file_path, "r") as f_in:
            lines = f_in.readlines()
        with open(config_file_path, "w") as f_out:
            for line in lines:
                for key, value in properties.items():
                    if line.startswith(key + "=") or \
                            (line.startswith("#") and line[1:].lstrip().startswith(key + "=")):
                        if value is True:
                            value = "true"
                        if value is False:
                            value = "false"
                        f_out.write("%s=%s\n" % (key, value))
                        break
                else:
                    f_out.write(line)

    @property
    def auth_enabled(self):
        """ Settable boolean property for enabling and disabling auth
        on this server.
        """
        return self.config("dbms.security.auth_enabled") == "true"

    @auth_enabled.setter
    def auth_enabled(self, value):
        self.set_config("dbms.security.auth_enabled", value)

    def update_password(self, user, password, new_password):
        """ Update the password for this server.

        :param user:
        :param password:
        :param new_password:
        :return:
        """
        request = Request("%suser/neo4j/password" % self.http_uri,
                          json_dumps({"password": new_password}, ensure_ascii=True).encode("utf-8"),
                          {"Authorization": "Basic " + b64encode((user + ":" + password).encode("utf-8")).decode("ascii"),
                           "Content-Type": "application/json"})
        try:
            urlopen(request).read()
        except HTTPError as error:
            raise Unauthorized("Cannot update password [%s]" % error)

    @property
    def http_port(self):
        """ The port on which this server expects HTTP communication.
        """
        return NotImplemented

    @http_port.setter
    def http_port(self, port):
        """ Set the port on which this server expects HTTP communication.
        """

    @property
    def http_uri(self):
        """ The full HTTP URI for this server.
        """
        return "http://localhost:%d/" % self.http_port

    def delete_store(self, force=False):
        """ Delete the store directory for this server.

        :param force:
        """
        if force or not self.running():
            try:
                rmtree(self.store_path, ignore_errors=force)
            except FileNotFoundError:
                pass
        else:
            raise RuntimeError("Refusing to drop database store while server is running")

    def start(self):
        """ Start the server.
        """
        try:
            out = check_output("%s start" % self.control_script, shell=True)
        except CalledProcessError as error:
            if error.returncode == 2:
                raise OSError("Another process is listening on the server port")
            elif error.returncode == 512:
                raise OSError("Another server process is already running")
            else:
                raise OSError("An error occurred while trying to start "
                              "the server [%s]" % error.returncode)
        else:
            pid = None
            for line in out.decode("utf-8").splitlines(False):
                if line.startswith("process"):
                    numbers = number_in_brackets.search(line).groups()
                    if numbers:
                        pid = int(numbers[0])
                elif "(pid " in line:
                    pid = int(line.partition("(pid ")[-1].partition(")")[0])
            running = False
            port = self.http_port
            t = 0
            while not running and t < 30:
                try:
                    s = create_connection(("localhost", port))
                except IOError:
                    sleep(1)
                    t += 1
                else:
                    s.close()
                    running = True
            return pid

    def stop(self):
        """ Stop the server.
        """
        try:
            check_output(("%s stop" % self.control_script), shell=True)
        except CalledProcessError as error:
            raise OSError("An error occurred while trying to stop the server "
                          "[%s]" % error.returncode)

    def restart(self):
        """ Restart the server.
        """
        self.stop()
        return self.start()

    def running(self):
        """ The PID of the current executing process for this server.
        """
        try:
            out = check_output(("%s status" % self.control_script), shell=True)
        except CalledProcessError as error:
            if error.returncode == 3:
                return None
            else:
                raise OSError("An error occurred while trying to query the "
                              "server status [%s]" % error.returncode)
        else:
            p = None
            for line in out.decode("utf-8").splitlines(False):
                if "running" in line:
                    p = int(line.rpartition(" ")[-1])
            return p

    def info(self, key):
        """ Look up an item of server information from a running server.

        :param key: the key of the item to look up
        """
        try:
            out = check_output("%s info" % self.control_script, shell=True)
        except CalledProcessError as error:
            if error.returncode == 3:
                return None
            else:
                raise OSError("An error occurred while trying to fetch server "
                              "info [%s]" % error.returncode)
        else:
            for line in out.decode("utf-8").splitlines(False):
                try:
                    colon = line.index(":")
                except ValueError:
                    pass
                else:
                    k = line[:colon]
                    v = line[colon+1:].lstrip()
                    if k == "CLASSPATH":
                        v = v.split(":")
                    if k == key:
                        return v


class GraphServerV2(GraphServer):

    config_file = "neo4j-server.properties"

    @property
    def http_port(self):
        port = None
        if self.running():
            port = self.info("NEO4J_SERVER_PORT")
        if port is None:
            port = self.config("org.neo4j.server.webserver.port")
        try:
            return int(port)
        except (TypeError, ValueError):
            return None

    @http_port.setter
    def http_port(self, port):
        self.set_config("org.neo4j.server.webserver.port", port)

    @property
    def store_path(self):
        return path_join(self.home, self.config("org.neo4j.server.database.location"))


class GraphServerV3(GraphServer):

    config_file = "neo4j.conf"

    @property
    def http_port(self):
        port = None
        if self.running():
            port = self.info("NEO4J_SERVER_PORT")
        if port is None:
            http_address = self.config("dbms.connector.http.address")
            if http_address:
                host, _, port = http_address.partition(":")
            else:
                port = self.default_http_port
        try:
            return int(port)
        except (TypeError, ValueError):
            return None

    @http_port.setter
    def http_port(self, port):
        http_address = self.config("dbms.connector.http.address")
        if http_address:
            host, _, _ = http_address.partition(":")
        else:
            host = "localhost"
        self.set_config("dbms.connector.http.address", "%s:%d" % (host, port))

    @property
    def store_path(self):
        return path_join(self.home, "data", "databases",
                         self.config("dbms.active_database", "graph.db"))


class Commander(object):

    epilog = "Report bugs to nigel@py2neo.org"

    def __init__(self, out=None, err=None):
        self.out = out or stdout
        self.err = err or stderr

    def write(self, s):
        self.out.write(s)

    def write_line(self, s):
        self.out.write(s)
        self.out.write(linesep)

    def write_err(self, s):
        self.err.write(s)

    def write_err_line(self, s):
        self.err.write(s)
        self.err.write(linesep)

    def usage(self, script):
        script = basename(script)
        self.write_line("usage: %s <command> <arguments>" % script)
        self.write_line("       %s help <command>" % script)
        self.write_line("")
        self.write_line("commands:")
        for attr in sorted(dir(self)):
            method = getattr(self, attr)
            if callable(method) and not attr.startswith("_") and method.__doc__:
                doc = dedent(method.__doc__).strip()
                self.write_line("    " + doc[6:].strip())
        self.write_line("")
        self.write_line(
                "Many commands can take '.' as a server name. This operates on the server\n"
                "located in the current directory. For example:\n"
                "\n"
                "    neokit disable-auth .")
        if self.epilog:
            self.write_line("")
            self.write_line(self.epilog)

    def execute(self, *args):
        try:
            command = args[1]
        except IndexError:
            self.usage(args[0])
            return
        command = command.replace("-", "_")
        if command == "help":
            command = args[2]
            args = [args[0], command, "--help"]
        try:
            method = getattr(self, command)
        except AttributeError:
            self.write_err_line("Unknown command %r" % command)
            exit(1)
        else:
            try:
                return method(*args[1:]) or 0
            except Exception as err:
                self.write_err_line("Error: %s" % err)
                exit(1)

    def parser(self, script):
        return ArgumentParser(prog=script, epilog=self.epilog)

    def versions(self, *args):
        """ usage: versions
        """
        parser = self.parser(args[0])
        parser.description = "List all available Neo4j versions"
        parser.parse_args(args[1:])
        for version in versions:
            self.write(version)
            aliases = []
            for alias, original in version_aliases.items():
                if original == version:
                    aliases.append(alias)
            if aliases:
                self.write(" (%s)" % ", ".join(sorted(aliases)))
            self.write(linesep)

    def download(self, *args):
        """ usage: download [<version>]
        """
        parser = self.parser(args[0])
        parser.description = "Download a Neo4j server package"
        parser.add_argument("version", nargs="?", help="Neo4j version")
        parsed = parser.parse_args(args[1:])
        self.write_line(Package(version=parsed.version).download())

    def install(self, *args):
        """ usage: install <server> [<version>]
        """
        parser = self.parser(args[0])
        parser.description = "Install a Neo4j server"
        parser.add_argument("server", help="server name")
        parser.add_argument("version", nargs="?", help="Neo4j version")
        parsed = parser.parse_args(args[1:])
        server = Warehouse().install(parsed.server, version=parsed.version)
        self.write_line(server.home)

    def uninstall(self, *args):
        """ usage: uninstall <server>
        """
        parser = self.parser(args[0])
        parser.description = "Uninstall a Neo4j server"
        parser.add_argument("server", help="server name")
        parsed = parser.parse_args(args[1:])
        server_name = parsed.server
        warehouse = Warehouse()
        server = warehouse.get(server_name)
        if server.running():
            server.stop()
        warehouse.uninstall(server_name)

    def list(self, *args):
        """ usage: list
        """
        parser = self.parser(args[0])
        parser.description = "List all installed Neo4j servers"
        parser.parse_args(args[1:])
        for name in sorted(Warehouse().directory()):
            self.write_line(name)

    def rename(self, *args):
        """ usage: rename <server> <new-name>
        """
        parser = self.parser(args[0])
        parser.description = "Rename a Neo4j server"
        parser.add_argument("server", help="server name")
        parser.add_argument("new_name", help="new server name")
        parsed = parser.parse_args(args[1:])
        Warehouse().rename(parsed.server, parsed.new_name)

    def start(self, *args):
        """ usage: start <server>
        """
        parser = self.parser(args[0])
        parser.description = "Start a Neo4j server"
        parser.add_argument("server", help="server name")
        parsed = parser.parse_args(args[1:])
        if parsed.server == ".":
            server = GraphServer()
        else:
            server = Warehouse().get(parsed.server)
        if server.running():
            self.write_err_line("Server already running")
            return SERVER_ALREADY_RUNNING
        else:
            pid = server.start()
            self.write_line("%d" % pid)

    def stop(self, *args):
        """ usage: stop <server>
        """
        parser = self.parser(args[0])
        parser.description = "Stop a Neo4j server"
        parser.add_argument("server", help="server name")
        parsed = parser.parse_args(args[1:])
        if parsed.server == ".":
            server = GraphServer()
        else:
            server = Warehouse().get(parsed.server)
        if server.running():
            server.stop()
        else:
            self.write_err_line("Server not running")
            return SERVER_NOT_RUNNING

    def restart(self, *args):
        """ usage: restart <server>
        """
        parser = self.parser(args[0])
        parser.description = "Start or restart a Neo4j server"
        parser.add_argument("server", help="server name")
        parsed = parser.parse_args(args[1:])
        if parsed.server == ".":
            server = GraphServer()
        else:
            server = Warehouse().get(parsed.server)
        if server.running():
            pid = server.restart()
        else:
            pid = server.start()
        self.write_line("%d" % pid)

    def run(self, *args):
        """ usage: run <server> <command>
        """
        parser = self.parser(args[0])
        parser.description = "Run a command against a Neo4j server"
        parser.add_argument("server", help="server name")
        parser.add_argument("command", nargs="+", help="command to run")
        parsed = parser.parse_args(args[1:])
        with move_file(path_join(expanduser("~"), ".neo4j", "known_hosts")):
            if parsed.server == ".":
                server = GraphServer()
            else:
                server = Warehouse().get(parsed.server)
            if server.running():
                self.write_err_line("Server already running")
                return SERVER_ALREADY_RUNNING
            else:
                server.start()
                try:
                    return call(parsed.command)
                finally:
                    server.stop()

    def enable_auth(self, *args):
        """ usage: enable-auth <server>
        """
        parser = self.parser(args[0])
        parser.description = "Enable auth on a Neo4j server"
        parser.add_argument("server", help="server name")
        parsed = parser.parse_args(args[1:])
        if parsed.server == ".":
            server = GraphServer()
        else:
            server = Warehouse().get(parsed.server)
        server.auth_enabled = True

    def disable_auth(self, *args):
        """ usage: disable-auth <server>
        """
        parser = self.parser(args[0])
        parser.description = "Disable auth on a Neo4j server"
        parser.add_argument("server", help="server name")
        parsed = parser.parse_args(args[1:])
        if parsed.server == ".":
            server = GraphServer()
        else:
            server = Warehouse().get(parsed.server)
        server.auth_enabled = False

    def update_password(self, *args):
        """ usage: update-password <server> <user> <password> <new_password>
        """
        parser = self.parser(args[0])
        parser.description = "Update a password for a Neo4j server"
        parser.add_argument("server", help="server name")
        parser.add_argument("user", help="user name")
        parser.add_argument("password", help="current password")
        parser.add_argument("new_password", help="new password")
        parsed = parser.parse_args(args[1:])
        if parsed.server == ".":
            server = GraphServer()
        else:
            server = Warehouse().get(parsed.server)
        already_running = server.running()
        if not already_running:
            server.start()
        try:
            server.update_password(parsed.user, parsed.password, parsed.new_password)
        except Unauthorized as error:
            self.write_err_line("%s" % error)
            return SERVER_AUTH_FAILURE
        finally:
            if not already_running:
                server.stop()


def main(args=None, out=None, err=None):
    exit_status = Commander(out, err).execute(*args or argv)
    exit(exit_status)


if __name__ == "__main__":
    main()

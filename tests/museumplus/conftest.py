import time
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from threading import Event, Thread

import aiohttp
import lxml.etree
import pytest


@pytest.fixture(scope="function")
def museum_object(load_museum_object):
    return load_museum_object(object_id="1234567")


@pytest.fixture(scope="function")
def museum_attachment(load_museum_attachment):
    return load_museum_attachment(attachment_id="1234567001")


# Defined here for Python 3.6 compatibility
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class MockMuseumPlusHandler(BaseHTTPRequestHandler):
    def make_response(self, path):
        content_type = self.headers["Content-Type"]
        content = None

        if content_type == "application/xml":
            path = path.with_suffix(".xml")

        with open(path, "rb") as f:
            content = f.read()

        if content:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        """
        For GET requests, retrieve a file from the mocked test data directory
        and return it as-is
        """
        path = Path(self.server.museumplus.base_path) / Path(self.path[1:])
        self.make_response(path)

        # Keep track of how many times each request has been made
        self.server.museumplus.log_request(
            method="GET", url=self.path, content=None
        )

    def do_POST(self):
        """
        For POST requests, retrieve and return files in ascending order from
        a specific directory to mimic changes between requests
        """
        sequence_id = self.server.museumplus.request_counters[self.path]

        path = Path(
            self.server.museumplus.base_path
        ) / Path(self.path[1:]) / str(sequence_id)

        self.make_response(path)

        # Keep track of how many times each request has been made
        request_content = self.rfile.read(int(self.headers["Content-Length"]))
        self.server.museumplus.log_request(
            method="POST", url=self.path, content=request_content
        )

    def do_PUT(self):
        """
        For PUT requests, simply return a 204 No Content response
        """
        # Keep track of how many times each request has been made
        request_content = self.rfile.read(int(self.headers["Content-Length"]))
        self.server.museumplus.log_request(
            method="PUT", url=self.path, content=request_content
        )

        # Check if a corresponding Object exists; if so, return 204,
        # otherwise 404
        object_id = self.path.split("/")[-2]
        object_id_xml_path = (
            Path(self.server.museumplus.base_path)
            / "module" / "Object" / f"{object_id}.xml"
        )

        if object_id_xml_path.exists():
            self.send_response(204)
        else:
            self.send_response(404)

        self.end_headers()


class MockMuseumPlus:
    """
    Mock HTTP server that returns XML documents from a given path.

    The directory structure underneath the path maps to the URL used
    in MuseumPlus HTTP API to retrieve XML documents.

    For example, a GET request asking for a XML document from
    https://{MUSEUMPLUS_URL}/module/Object/1234
    will try to read and return a XML file from the local path
    {PATH}/module/Object/1234.xml
    """
    def __init__(self, base_path, port):
        self.base_path = base_path
        self.port = port

        self.request_counters = defaultdict(int)
        self.requests = []

        self.server = ThreadingHTTPServer(
            ("127.0.0.1", port), MockMuseumPlusHandler
        )
        self.server.timeout = 0.05
        self.server.museumplus = self

    def log_request(self, method, url, content):
        """
        Log a received request to allow it to be examined by tests afterwards
        """
        self.request_counters[url] += 1
        self.requests.append({
            "method": method,
            "url": url,
            "content": content
        })

    def serve_requests(self):
        self.server.handle_request()


def launch_mock_thread(mock_server, shutdown_flag):
    while not shutdown_flag.is_set():
        mock_server.serve_requests()
        time.sleep(0.02)

    mock_server.server.server_close()


@pytest.fixture(scope="function")
def launch_mock_museumplus(unused_tcp_port_factory, monkeypatch, tmp_path):
    shutdown_flag = Event()
    threads = []

    def func(path):
        port = unused_tcp_port_factory()
        attrs = (
            "passari.museumplus.db.MUSEUMPLUS_URL",
            "passari.museumplus.connection.MUSEUMPLUS_URL",
            "passari.museumplus.search.MUSEUMPLUS_URL",
            "passari.museumplus.fields.MUSEUMPLUS_URL",
            "passari.dpres.package.MUSEUMPLUS_URL"
        )

        # Monkeypatch modules using the MuseumPlus URL
        for attr in attrs:
            monkeypatch.setattr(attr, f"http://127.0.0.1:{port}")

        mock_server = MockMuseumPlus(
            base_path=path, port=port
        )

        thread = Thread(
            target=launch_mock_thread,
            kwargs={
                "mock_server": mock_server, "shutdown_flag": shutdown_flag
            }
        )
        thread.start()
        threads.append(thread)

        return mock_server

    yield func
    shutdown_flag.set()

    for thread in threads:
        thread.join()


@pytest.fixture(scope="function")
def mock_museumplus(launch_mock_museumplus):
    return launch_mock_museumplus(
        Path(__file__).resolve().parent / "data" / "museumplus_mock"
    )


@pytest.fixture(scope="function")
async def museum_session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest.fixture(scope="function")
def load_museum_object(museum_session):
    from passari.museumplus.db import MuseumObject

    def func(object_id):
        path = (
            Path(__file__).resolve().parent
            / "data" / "museumplus_mock" / "module" / "Object"
            / f"{object_id}.xml"
        )
        with open(path, "rb") as f:
            etree = lxml.etree.parse(f)

        return MuseumObject(
            etree=etree,
            session=museum_session
        )

    return func


@pytest.fixture(scope="function")
def load_museum_attachment(museum_session):
    from passari.museumplus.db import MuseumAttachment

    def func(attachment_id):
        path = (
            Path(__file__).resolve().parent
            / "data" / "museumplus_mock" / "module" / "Multimedia"
            / f"{attachment_id}.xml"
        )
        with open(path, "rb") as f:
            etree = lxml.etree.parse(f)

        return MuseumAttachment(etree)

    return func

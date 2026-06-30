"""Unit tests for the XML API, exercised via Flask's test client.

No server and no Docker are needed: `app.test_client()` dispatches requests
through the WSGI app in-process, so these run in milliseconds.
"""
from xml.etree.ElementTree import fromstring

import pytest

from app import app as flask_app


@pytest.fixture
def client():
    """A fresh test client per test. `testing=True` surfaces errors instead of
    swallowing them into generic 500 pages."""
    flask_app.config.update(TESTING=True)
    return flask_app.test_client()


def test_health_returns_ok_xml(client):
    """/health must return 200, an XML content type, and <status>ok</status>."""
    resp = client.get("/health")

    assert resp.status_code == 200
    # The content type is part of the contract — consumers branch on it.
    assert resp.mimetype == "application/xml"
    # Parse rather than string-match, so we assert on structure, not formatting.
    root = fromstring(resp.data)
    assert root.tag == "health"
    assert root.findtext("status") == "ok"


def test_greet_defaults_to_world(client):
    """With no ?name, the greeting falls back to 'world'."""
    root = fromstring(client.get("/api/greet").data)
    assert root.findtext("message") == "Hello, world!"


def test_greet_uses_name_query_param(client):
    """The ?name query parameter is reflected into the message."""
    root = fromstring(client.get("/api/greet?name=Ada").data)
    assert root.findtext("message") == "Hello, Ada!"


def test_echo_reflects_json_as_xml(client):
    """A JSON object body is echoed back as <item key=...> elements."""
    resp = client.post("/api/echo", json={"color": "blue", "count": 3})

    assert resp.status_code == 200
    root = fromstring(resp.data)
    items = {item.get("key"): item.text for item in root.findall("item")}
    assert items == {"color": "blue", "count": "3"}


def test_echo_rejects_non_object_body(client):
    """A non-object JSON body (here, a list) is a client error -> 400 + XML error."""
    resp = client.post("/api/echo", json=[])

    assert resp.status_code == 400
    root = fromstring(resp.data)
    assert root.tag == "error"
    assert "JSON object" in (root.findtext("message") or "")

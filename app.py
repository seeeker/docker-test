"""A small Flask API that processes web requests and returns XML responses."""
from flask import Flask, request, Response
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.sax.saxutils import escape

app = Flask(__name__)


def xml_response(root: Element, status: int = 200) -> Response:
    """Serialize an ElementTree element to an XML HTTP response."""
    body = b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(root, encoding="utf-8")
    return Response(body, status=status, mimetype="application/xml")


@app.get("/health")
def health():
    """Liveness probe."""
    root = Element("health")
    SubElement(root, "status").text = "ok"
    return xml_response(root)


@app.get("/api/greet")
def greet():
    """Return an XML greeting. Example: /api/greet?name=Ada"""
    name = request.args.get("name", "world")
    root = Element("greeting")
    SubElement(root, "message").text = f"Hello, {name}!"
    return xml_response(root)


@app.post("/api/echo")
def echo():
    """Accept a JSON body and echo its key/value pairs back as XML."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        root = Element("error")
        SubElement(root, "message").text = "Request body must be a JSON object."
        return xml_response(root, status=400)

    root = Element("echo")
    for key, value in data.items():
        item = SubElement(root, "item", attrib={"key": escape(str(key))})
        item.text = str(value)
    return xml_response(root)


if __name__ == "__main__":
    # Development entrypoint; in the container we run via gunicorn (see Dockerfile).
    app.run(host="0.0.0.0", port=8000, debug=True)

import functools
import http.server
import threading
from pathlib import Path

import pytest

from scout import scout

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def base_url():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(FIXTURES))
    handler.log_message = lambda *a, **k: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_extracts_basic_fields(base_url):
    p = scout(f"{base_url}/company.html")
    assert p.title == "Acme Robotics"
    assert p.description == "Acme builds warehouse robots."
    assert "What we do" in p.headings


def test_sees_javascript_rendered_content(base_url):
    p = scout(f"{base_url}/company.html")
    assert "Our team" in p.headings
    assert "sales@acme.example" in p.emails


def test_finds_emails_and_social_links(base_url):
    p = scout(f"{base_url}/company.html")
    assert "hello@acme.example" in p.emails
    assert any("linkedin.com" in s for s in p.social_links)

#!/usr/bin/env python3
"""Sirve docs/ en localhost para verla en un navegador normal.

Las URLs del HTML son absolutas, así que al servirlas tal cual se cargarían los estilos del
WordPress. Aquí se reescriben solo en la respuesta: docs/ no cambia y no es lo que se publica.
"""
import io
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

DOCS = Path(__file__).resolve().parent.parent / "docs"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
ORIGIN_RE = re.compile(rb"https?:(\\?/\\?/)motricidadlaboral\.com")
TEXT_SUFFIXES = {".html", ".css", ".js", ".xml", ".json"}


def rewrite(body: bytes) -> bytes:
    return ORIGIN_RE.sub(lambda m: b"http:" + m.group(1) + b"localhost:%d" % PORT, body)


class Handler(SimpleHTTPRequestHandler):
    def send_body(self, status: int, content_type: str, body: bytes):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        return io.BytesIO(body)

    def send_head(self):
        path = Path(self.translate_path(self.path))
        if path.is_dir():
            if not urlsplit(self.path).path.endswith("/"):
                return super().send_head()
            path = path / "index.html"
        if not path.is_file():
            return self.send_body(404, "text/html", rewrite((DOCS / "404.html").read_bytes()))
        if path.suffix in TEXT_SUFFIXES:
            return self.send_body(200, self.guess_type(str(path)), rewrite(path.read_bytes()))
        return super().send_head()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"http://localhost:{PORT}/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=str(DOCS))).serve_forever()

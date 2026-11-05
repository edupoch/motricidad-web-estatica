#!/usr/bin/env python3
"""Descarga la web original a mirror/ sin modificarla. Debe ejecutarse con WordPress aún en marcha.

Solo sigue URLs de atributos HTML y de url() en CSS, nunca el contenido de <script>: el JS en línea
contiene cadenas que parecen enlaces, y cada 404 cuenta para el bloqueo por IP de Defender.
Se detiene en cuanto recibe un 403. Lo ya descargado no se vuelve a pedir.

Uso: mirror.py [--dry-run]   (--dry-run lista lo que pediría, sin usar la red)
"""
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://motricidadlaboral.com/"
HOST = "motricidadlaboral.com"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
OUT = Path(__file__).resolve().parent.parent / "mirror"
SITEMAPS = ["post", "page", "category", "post_tag"]
WAIT_SECONDS = 1.5
MAX_NOT_FOUND = 5
SKIP = re.compile(
    r"/(portfolio-item|portfolio_entries|wp-json|wp-admin|feed|xmlrpc\.php|wp-login\.php|comments"
    r"|cdn-cgi)(/|$)|^/entorno-activo/|medical\.woff2$|\.xml$"
)
SKIP_QUERY = re.compile(r"(^|&)(replytocom|p|s|wds_sitemap_styling)=")
# Solo los pide el JS, a menudo tras aceptar cookies, o aparecen en datos estructurados: no salen del rastreo.
EXTRA = [
    "wp-content/themes/enfold/framework/js/conditional_load/avia_google_maps_api.js",
    "wp-content/themes/enfold/js/html5shiv.js",
    "wp-includes/js/wp-emoji-release.min.js?ver=9db20bb0a742265afeaefc185aadd64e",
    "wp-content/uploads/2017/10/logo_motricidadlaboral_h-copia.png",
]
URL_ATTRS = {"href", "src", "poster", "data-src"}
CSS_URL = re.compile(r"""url\(\s*['"]?([^'")]+)""")


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if not value:
                continue
            if name in URL_ATTRS:
                self.urls.append(value)
            elif name in ("srcset", "data-srcset"):
                self.urls += [part.split()[0] for part in value.split(",") if part.strip()]
            elif name == "style":
                self.urls += CSS_URL.findall(value)


def in_scope(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https") or parts.netloc != HOST:
        return False
    return not SKIP.search(parts.path) and not SKIP_QUERY.search(parts.query)


def local_path(url):
    parts = urllib.parse.urlsplit(url)
    path = urllib.parse.unquote(parts.path).lstrip("/")
    if not path or path.endswith("/"):
        path += "index.html"
    if parts.query:
        path += "?" + urllib.parse.unquote(parts.query)
    return OUT / path


def links_in(url, path):
    data = path.read_bytes()
    if path.name.startswith("index.html"):
        parser = LinkParser()
        parser.feed(data.decode("utf-8", "replace"))
        found = parser.urls
    elif ".css" in path.name:
        found = CSS_URL.findall(data.decode("utf-8", "replace"))
    else:
        return []
    return [urllib.parse.urldefrag(urllib.parse.urljoin(url, u.strip())).url for u in found]


def fetch(url):
    safe = urllib.parse.quote(url, safe=":/?&=%#+,;@!$'()*~-._")
    req = urllib.request.Request(safe, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def crawl(seeds, dry_run):
    queue, seen, not_found = list(seeds), set(), []
    requested = []
    while queue:
        url = queue.pop(0)
        if url in seen or not in_scope(url):
            continue
        seen.add(url)
        path = local_path(url)
        if not path.is_file():
            requested.append(url)
            if dry_run:
                continue
            time.sleep(WAIT_SECONDS)
            try:
                data = fetch(url)
            except urllib.error.HTTPError as err:
                if err.code == 403:
                    sys.exit(f"403 en {url}: bloqueo activo, me detengo. Quedan {len(queue)} en cola.")
                not_found.append(url)
                print(f"{err.code} {url}")
                if len(not_found) >= MAX_NOT_FOUND:
                    sys.exit(f"Demasiados errores ({MAX_NOT_FOUND}): me detengo para no provocar un bloqueo.")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            print(f"ok {url}")
        queue += links_in(url, path)
    return requested, not_found


def fetch_special(dry_run):
    """Página 404 real y feed, fuera del rastreo normal."""
    if dry_run:
        return
    try:
        fetch(BASE + "esta-url-no-existe-404/")
    except urllib.error.HTTPError as err:
        if err.code == 403:
            sys.exit("403 al pedir la 404: bloqueo activo, me detengo.")
        (OUT / "404.html").write_bytes(err.read())
    (OUT / "feed").mkdir(exist_ok=True)
    (OUT / "feed" / "index.xml").write_bytes(fetch(BASE + "feed/"))


def main():
    dry_run = "--dry-run" in sys.argv
    seeds = [BASE] + [BASE + path for path in EXTRA]
    if dry_run:
        seeds += [p.parent.relative_to(OUT).as_posix() + "/" for p in OUT.rglob("index.html")]
        seeds = [urllib.parse.urljoin(BASE, s) for s in seeds if s != "./"]
    else:
        for name in SITEMAPS:
            xml = fetch(f"{BASE}{name}-sitemap.xml").decode("utf-8")
            seeds += [u for u in re.findall(r"<loc>([^<]+)", xml) if not re.search(r"\.(jpe?g|png|gif|webp)$", u)]
    requested, not_found = crawl(seeds, dry_run)
    fetch_special(dry_run)
    print(f"Pedidas: {len(requested)}. Con error: {len(not_found)}.")
    if dry_run:
        print("\n".join(requested))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Genera docs/ a partir de mirror/. Aplica solo las ediciones de SPEC.md: el resto se copia sin tocar."""
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIRROR = ROOT / "mirror"
DOCS = ROOT / "docs"
BASE = "https://motricidadlaboral.com/"
EMAIL = "info@motricidadlaboral.com"

ANALYTICS_RE = re.compile(
    r"<script type='text/javascript'>\s*\(function\(\$\) \{\s*/\*\s*check if google analytics.*?</script>\n?", re.S
)
RECAPTCHA_VAR = "var AviaReCAPTCHA_front = "
CF_CHALLENGE_RE = re.compile(r"<script>\(function\(\)\{function c\(\)\{var b=a\.contentDocument.*?</script>", re.S)
CF_EMAIL_RE = re.compile(
    r'<a href="/cdn-cgi/l/email-protection" class="__cf_email__" data-cfemail="([0-9a-f]+)">\[email&#160;protected\]</a>'
)
CF_EMAIL_LINK_RE = re.compile(r'href="/cdn-cgi/l/email-protection#([0-9a-f]+)"')
CF_DECODER_RE = re.compile(r'<script data-cfasync="false" src="/cdn-cgi/scripts/[^"]*email-decode\.min\.js"></script>')
CONTACT_FORM_RE = re.compile(
    r'<form action="https://motricidadlaboral\.com/contacto/".*?</form><div id="ajaxresponse_1"[^>]*></div>', re.S
)
CONTACT_LINK = f'<p><a href="mailto:{EMAIL}">{EMAIL}</a></p>'
PAGING_RE = re.compile(r"noticias/\?avia-element-paging=(\d+)")
ORIGIN_RE = re.compile(r"https?:(\\?/)\\?/motricidadlaboral\.com(\\?/)?")
# Texto visible y comentarios quedan fuera: solo se reescriben etiquetas, <style> y <script>.
MARKUP_RE = re.compile(r"<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<!--.*?-->|<[a-zA-Z][^>]*>", re.S)
# Necesitan la URL absoluta para buscadores y redes sociales.
KEEP_ABSOLUTE_RE = re.compile(
    r"""^<!--|^<meta\b|^<script\b[^>]*application/ld\+json|^<link\b(?![^>]*\brel=["']?(?:stylesheet|preload|icon|apple-touch-icon))""",
    re.I,
)

applied = Counter()


def decode_email(encoded):
    key = int(encoded[:2], 16)
    data = bytes(int(encoded[i:i + 2], 16) ^ key for i in range(2, len(encoded), 2))
    return data.decode("utf-8")


def sub_counted(name, pattern, repl, html, required=False):
    result, count = pattern.subn(repl, html)
    if required and count == 0:
        raise ValueError(f"No se ha encontrado: {name}")
    applied[name] += count
    return result


def remove_recaptcha_var(html):
    """Sin esta variable, el JS del tema (que no se toca) no intenta cargar reCAPTCHA.

    Comparte línea con la configuración del banner de cookies: el final se obtiene leyendo el JSON.
    """
    start = html.find(RECAPTCHA_VAR)
    if start < 0:
        raise ValueError("No se ha encontrado: recaptcha")
    _, end = json.JSONDecoder().raw_decode(html, start + len(RECAPTCHA_VAR))
    if html[end] != ";":
        raise ValueError("Formato inesperado en la variable de reCAPTCHA")
    applied["recaptcha"] += 1
    return html[:start] + html[end + 1:]


def to_prefix(text, prefix):
    """Cambia el dominio por un prefijo de ruta, respetando la forma escapada de los JSON (\\/)."""

    def repl(match):
        slash = match.group(1)
        return prefix.replace("/", slash)

    return ORIGIN_RE.subn(repl, text)


def relative_prefix(target):
    """Prefijo hasta la raíz de la web. La 404 se sirve desde cualquier ruta: solo puede ir desde la raíz."""
    if target == "404.html":
        return "/"
    depth = target.count("/")
    return "../" * depth or "./"


def same_origin_html(html, target):
    prefix = relative_prefix(target)

    def repl(match):
        fragment = match.group(0)
        if KEEP_ABSOLUTE_RE.match(fragment):
            return fragment
        result, count = to_prefix(fragment, prefix)
        applied["url_html"] += count
        return result

    return MARKUP_RE.sub(repl, html)


def same_origin_css(css, target):
    result, count = to_prefix(css, relative_prefix(target))
    applied["url_css"] += count
    return result


def transform(html, rel):
    html = sub_counted("analytics", ANALYTICS_RE, "", html, required=True)
    html = remove_recaptcha_var(html)
    html = sub_counted("reto_cloudflare", CF_CHALLENGE_RE, "", html)
    html = sub_counted("correo_texto", CF_EMAIL_RE, lambda m: decode_email(m.group(1)), html)
    html = sub_counted("correo_enlace", CF_EMAIL_LINK_RE, lambda m: f'href="mailto:{decode_email(m.group(1))}"', html)
    html = sub_counted("script_correo", CF_DECODER_RE, "", html)
    if rel == "contacto/index.html":
        html = sub_counted("formulario", CONTACT_FORM_RE, CONTACT_LINK, html, required=True)
    return sub_counted("paginacion", PAGING_RE, r"noticias/page/\1/", html)


def target_for(rel):
    """Ruta en docs/: sin parámetro de versión, y las páginas de /noticias/ en /noticias/page/N/."""
    paging = re.fullmatch(r"noticias/index\.html\?avia-element-paging=(\d+)", rel)
    if paging:
        return f"noticias/page/{paging.group(1)}/index.html"
    return rel.split("?", 1)[0]


def is_html(rel):
    return rel == "404.html" or rel.split("?", 1)[0].endswith("index.html")


def main():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    sources = sorted(p for p in MIRROR.rglob("*") if p.is_file() and p.relative_to(MIRROR).parts[0] != "cdn-cgi")
    # Primero los que no llevan parámetro: si dos variantes difieren, debe verse.
    sources.sort(key=lambda p: "?" in p.name)
    written = {}
    urls = []
    for source in sources:
        rel = source.relative_to(MIRROR).as_posix()
        target = target_for(rel)
        dest = DOCS / target
        if is_html(rel):
            data = same_origin_html(transform(source.read_bytes().decode("utf-8"), rel), target).encode("utf-8")
            if target != "404.html":
                urls.append(target.removesuffix("index.html"))
        elif target.endswith(".css") and ORIGIN_RE.search(source.read_bytes().decode("utf-8", "replace")):
            data = same_origin_css(source.read_bytes().decode("utf-8"), target).encode("utf-8")
        else:
            data = source.read_bytes()
        if target in written:
            if written[target] != data:
                sys.exit(f"Dos variantes de {target} tienen contenido distinto")
            continue
        written[target] = data
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    (DOCS / ".nojekyll").write_bytes(b"")
    entries = "".join(f"<url><loc>{BASE}{u}</loc></url>\n" for u in sorted(urls))
    (DOCS / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}</urlset>\n',
        encoding="utf-8",
    )
    print(f"Archivos: {len(written)}. Páginas: {len(urls)}.")
    print(dict(applied))


if __name__ == "__main__":
    main()

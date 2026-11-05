#!/usr/bin/env python3
"""Comprueba que docs/ es copia exacta de mirror/ salvo las ediciones de SPEC.md, sin usar el código de build.py."""
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIRROR, DOCS = ROOT / "mirror", ROOT / "docs"
# Cada línea eliminada o añadida debe pertenecer a una edición prevista.
ALLOWED = re.compile(
    r"analytics|gtag|dataLayer|UA-53062585|ga-disable|email-protection|email-decode|__CF\$cv|avia-element-paging"
    r"|noticias/page/\d+/|avia_ajax_form|mailto:|[a-z]+@motricidadlaboral\.com",
    re.I,
)
INLINE_REMOVED = re.compile(
    r'<script data-cfasync="false" src="/cdn-cgi/[^"]*email-decode\.min\.js"></script>'
    r"|<script>\(function\(\)\{function c\(\)\{var b=a\.contentDocument.*?</script>",
    re.S,
)


def without_inline_removed(html):
    html = INLINE_REMOVED.sub("", html)
    marker = "var AviaReCAPTCHA_front = "
    start = html.find(marker)
    if start < 0:
        return html
    _, end = json.JSONDecoder().raw_decode(html, start + len(marker))
    return html[:start] + html[end + 1:]


errors = []
checked = {"binarios": 0, "html": 0}
hunks = 0
for source in sorted(p for p in MIRROR.rglob("*") if p.is_file()):
    rel = source.relative_to(MIRROR).as_posix()
    if rel.startswith("cdn-cgi/"):
        continue
    paging = re.fullmatch(r"noticias/index\.html\?avia-element-paging=(\d+)", rel)
    target = DOCS / (f"noticias/page/{paging.group(1)}/index.html" if paging else rel.split("?", 1)[0])
    if not target.is_file():
        errors.append(f"Falta {target}")
    elif rel == "404.html" or rel.split("?", 1)[0].endswith("index.html"):
        checked["html"] += 1
        # Estos fragmentos comparten línea con otro marcado: se retiran para comparar el resto de la línea.
        a = without_inline_removed(source.read_text(encoding="utf-8")).splitlines()
        b = target.read_text(encoding="utf-8").splitlines()
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if op == "equal":
                continue
            hunks += 1
            changed = a[i1:i2] + b[j1:j2]
            text = "\n".join(changed)
            is_analytics_block = "check if google analytics" in text and "avia-cookie-settings-changed" in text
            if not is_analytics_block:
                for line in changed:
                    if line.strip() and not ALLOWED.search(line):
                        errors.append(f"{rel}: cambio no previsto: {line[:140]}")
    else:
        checked["binarios"] += 1
        if hashlib.sha256(source.read_bytes()).digest() != hashlib.sha256(target.read_bytes()).digest():
            errors.append(f"Distinto: {rel}")
print(checked, "bloques cambiados:", hunks)
print("\n".join(errors[:40]))
sys.exit(1 if errors else 0)

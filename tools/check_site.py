#!/usr/bin/env python3
"""Check the published site in site/ before it is deployed.

Run from anywhere:  python3 tools/check_site.py
Exit status 0 means every check passed; 1 means at least one failed.
Python 3 standard library only, no network access.

Checks:
1. site/ is up to date: rebuilding the diagram and the pages from src/
   gives exactly the files committed in site/ (and src/partials/).
2. Internal links work: every local href/src in the HTML, every url() in
   the CSS and every sitemap entry points to a file that exists, and every
   #fragment points to an id on the target page. Same for aria-labelledby
   and aria-describedby references.
3. The pages fit the Content Security Policy in site/_headers: no <script>,
   no <style> element, no style="" attribute, no resource from another site.
4. site/_headers sets the expected security headers for every path.
5. site/.well-known/security.txt (RFC 9116) has Contact and Expires, and
   Expires is at least MIN_DAYS days away.
"""
import datetime
import html.parser
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DOMAIN_HOSTS = {"sovereigninfralab.com", "www.sovereigninfralab.com"}
MIN_DAYS = 60
REQUIRED_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
]

problems = []


def fail(message):
    problems.append(message)


def rel(path):
    return path.relative_to(ROOT).as_posix()


# 1. site/ is up to date --------------------------------------------------

def check_build():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        diagram = tmp / "edge-diagram.html"
        subprocess.run([sys.executable, str(ROOT / "tools" / "diagram.py"), str(diagram)],
                       check=True, stdout=subprocess.DEVNULL)
        committed = ROOT / "src" / "partials" / "edge-diagram.html"
        if diagram.read_bytes() != committed.read_bytes():
            fail(f"{rel(committed)} is out of date: run python3 tools/diagram.py")

        out = tmp / "site"
        subprocess.run([sys.executable, str(ROOT / "tools" / "build.py"), str(out)],
                       check=True, stdout=subprocess.DEVNULL)
        built = {p.relative_to(out) for p in out.rglob("*") if p.is_file()}
        for name in sorted(built):
            target = SITE / name
            if not target.is_file():
                fail(f"site/{name.as_posix()} is missing: run python3 tools/build.py")
            elif target.read_bytes() != (out / name).read_bytes():
                fail(f"site/{name.as_posix()} is out of date: run python3 tools/build.py")
        # Generated kinds of file in site/ that no page produces any more.
        for path in sorted(SITE.rglob("*.html")) + [SITE / "sitemap.xml"]:
            name = path.relative_to(SITE)
            if path.is_file() and name not in built:
                fail(f"site/{name.as_posix()} has no source page in src/pages/")


# 2 and 3. Links and CSP fit ----------------------------------------------

class Page(html.parser.HTMLParser):
    LINK_ATTRS = {"href", "src"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []        # (tag, attr, value)
        self.aria_refs = []    # id references
        self.scripts = 0
        self.styles = 0
        self.style_attrs = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "script":
            self.scripts += 1
        if tag == "style":
            self.styles += 1
        if "style" in attrs:
            self.style_attrs += 1
        for name in self.LINK_ATTRS & attrs.keys():
            self.links.append((tag, name, attrs[name] or ""))
        for name in ("aria-labelledby", "aria-describedby"):
            if attrs.get(name):
                self.aria_refs.extend(attrs[name].split())

    handle_startendtag = handle_starttag


def resolve(url_path):
    """Map a URL path to the file Cloudflare would serve, or None."""
    path = urllib.parse.unquote(url_path)
    candidate = SITE / path.lstrip("/")
    if path.endswith("/"):
        candidate = candidate / "index.html"
    if candidate.is_file():
        return candidate
    if (candidate / "index.html").is_file():   # html_handling: auto-trailing-slash
        return candidate / "index.html"
    if candidate.with_suffix(".html").is_file():
        return candidate.with_suffix(".html")
    return None


def check_pages():
    pages = {}
    for path in sorted(SITE.rglob("*.html")):
        parser = Page()
        parser.feed(path.read_text(encoding="utf-8"))
        pages[path] = parser

    for path, page in pages.items():
        where = rel(path)
        if page.scripts:
            fail(f"{where}: <script> is blocked by the Content Security Policy")
        if page.styles:
            fail(f"{where}: <style> is blocked by the Content Security Policy (use site/css/site.css)")
        if page.style_attrs:
            fail(f"{where}: style=\"\" attributes are blocked by the Content Security Policy")
        for ref in page.aria_refs:
            if ref not in page.ids:
                fail(f"{where}: aria reference to missing id \"{ref}\"")

        for tag, attr, value in page.links:
            parts = urllib.parse.urlsplit(value)
            if parts.scheme in ("mailto", "tel"):
                continue
            external = parts.scheme in ("http", "https") and parts.hostname not in DOMAIN_HOSTS
            if external:
                # Links to other sites are fine; loading resources from them is not.
                if tag != "a":
                    fail(f"{where}: <{tag} {attr}> loads {value} from another site")
                continue
            if parts.scheme and parts.scheme not in ("http", "https"):
                fail(f"{where}: unexpected link scheme in {value}")
                continue
            if not parts.path and parts.fragment:
                if parts.fragment not in page.ids:
                    fail(f"{where}: link #{parts.fragment} has no matching id")
                continue
            target = resolve(parts.path) if parts.path.startswith("/") else resolve(
                urllib.parse.urljoin("/" + path.relative_to(SITE).as_posix(), parts.path))
            if target is None:
                fail(f"{where}: broken link {value}")
            elif parts.fragment and target.suffix == ".html" and parts.fragment not in pages[target].ids:
                fail(f"{where}: link {value} points to a missing id on {rel(target)}")

    css = SITE / "css" / "site.css"
    for url in re.findall(r"url\(\s*['\"]?([^'\")]+)", css.read_text(encoding="utf-8")):
        if url.startswith("data:"):
            continue
        if re.match(r"^[a-z]+://", url):
            fail(f"{rel(css)}: url({url}) loads from another site")
        elif resolve(url if url.startswith("/") else "/css/" + url) is None:
            fail(f"{rel(css)}: url({url}) does not exist")

    sitemap = SITE / "sitemap.xml"
    for loc in re.findall(r"<loc>([^<]+)</loc>", sitemap.read_text(encoding="utf-8")):
        parts = urllib.parse.urlsplit(loc)
        if parts.hostname not in DOMAIN_HOSTS or resolve(parts.path) is None:
            fail(f"site/sitemap.xml: {loc} does not resolve to a page")


# 4. Security headers -----------------------------------------------------

def check_headers():
    path = SITE / "_headers"
    blocks, current = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace():
            current = line.strip()
            blocks[current] = {}
        elif current is not None:
            name, _, value = line.strip().partition(":")
            blocks[current][name.strip().lower()] = value.strip()
    all_paths = blocks.get("/*", {})
    for name in REQUIRED_HEADERS:
        if name.lower() not in all_paths:
            fail(f"site/_headers: the /* rule does not set {name}")
    csp = all_paths.get("content-security-policy", "")
    for directive in ("default-src 'none'", "frame-ancestors 'none'", "base-uri 'none'"):
        if directive not in csp:
            fail(f"site/_headers: Content-Security-Policy no longer contains {directive}")


# 5. security.txt -----------------------------------------------------------

def check_security_txt():
    path = SITE / ".well-known" / "security.txt"
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        name, sep, value = line.partition(":")
        if sep and not line.startswith("#"):
            fields.setdefault(name.strip().lower(), []).append(value.strip())
    if not fields.get("contact"):
        fail(f"{rel(path)}: no Contact field")
    expires = fields.get("expires", [])
    if len(expires) != 1:
        fail(f"{rel(path)}: needs exactly one Expires field")
        return
    try:
        when = datetime.datetime.fromisoformat(expires[0].replace("Z", "+00:00"))
    except ValueError:
        fail(f"{rel(path)}: Expires is not a valid date: {expires[0]}")
        return
    now = datetime.datetime.now(datetime.timezone.utc)
    days = (when - now).days
    if days < MIN_DAYS:
        fail(f"{rel(path)}: Expires is {days} days away (minimum {MIN_DAYS}); set a new date less than a year ahead")
    elif days > 366:
        fail(f"{rel(path)}: Expires is more than a year away; RFC 9116 recommends less than a year")


def main():
    check_build()
    check_pages()
    check_headers()
    check_security_txt()
    if problems:
        print(f"{len(problems)} problem(s) found:")
        for message in problems:
            print("  -", message)
        return 1
    print("All site checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Assemble the static SISL website from page bodies.

Each file in src/pages/ starts with header lines:
    title: ...
    description: ...
    path: /what-we-do/        (URL path; "/" for home, "/404.html" for the error page)
    page: home                (optional; added as a class on <body>)
followed by a line containing only "---" and then the HTML body of <main>.
A line "<!-- include: NAME -->" in a page is replaced by src/partials/NAME.html
(run tools/diagram.py first to regenerate the home-page diagram).
Output goes to site/ as plain HTML, so the published site needs no build step.
Python 3 standard library only.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site"
DOMAIN = "https://sovereigninfralab.com"

NAV = [
    ("/what-we-do/", "What we do"),
    ("/why-it-matters/", "Why it matters"),
    ("/research/", "Research"),
    ("/about/", "About"),
    ("/contact/", "Contact"),
]

BRAND_MARK = (
    '<svg class="brand-mark" viewBox="0 0 32 32" aria-hidden="true" focusable="false">'
    '<rect x="13" y="3" width="6" height="26" rx="1" class="bm-band"/>'
    '<path d="M3 9H29M3 16H29" class="bm-pass"/>'
    '<path d="M3 23H13" class="bm-stop"/>'
    "</svg>"
)

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
{canonical}<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/fonts/ibm-plex-sans-condensed-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/source-serif-4-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/css/site.css">
<meta name="theme-color" content="#17202b">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Sovereign Infrastructure Software Lab, LLC">
{og_url}</head>
<body class="{body_class}">
<a class="skip" href="#main">Skip to main content</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="/"{home_current}>{brand_mark}<span class="brand-short">SISL</span><span class="brand-long">Sovereign Infrastructure Software Lab</span></a>
    <nav class="site-nav" aria-label="Main">
      <ul>
{nav}
      </ul>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap footer-inner">
    <div class="footer-id">
      <p class="footer-name">Sovereign Infrastructure Software Lab, LLC</p>
      <p>20130 Lakeview Center Plaza, Suite 400<br>Ashburn, Virginia 20147</p>
    </div>
    <ul class="footer-links">
      <li><a href="/contact/">Contact</a></li>
      <li><a href="/privacy/">Privacy</a></li>
      <li><a href="/.well-known/security.txt">Security contact</a></li>
      <li><a href="https://github.com/sovereigninfralab">GitHub</a></li>
    </ul>
    <p class="footer-legal">&copy; 2026 Sovereign Infrastructure Software Lab, LLC &middot; Ashburn, Virginia</p>
  </div>
</footer>
</body>
</html>
"""

INCLUDE = re.compile(r"^[ \t]*<!-- include: ([a-z0-9-]+) -->[ \t]*$", re.M)


def parse(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    head, body = text.split("\n---\n", 1)
    meta = {}
    for line in head.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    body = INCLUDE.sub(lambda m: (ROOT / "src" / "partials" / f"{m.group(1)}.html").read_text(encoding="utf-8").rstrip("\n"), body)
    return meta, body.strip("\n")


def render(meta, body):
    url_path = meta["path"]
    nav_lines = []
    for href, label in NAV:
        current = ' aria-current="page"' if href == url_path else ""
        nav_lines.append(f'        <li><a href="{href}"{current}>{label}</a></li>')
    is_404 = url_path == "/404.html"
    canonical = "" if is_404 else f'<link rel="canonical" href="{DOMAIN}{url_path}">\n'
    og_url = "" if is_404 else f'<meta property="og:url" content="{DOMAIN}{url_path}">\n'
    return TEMPLATE.format(
        title=meta["title"],
        description=meta["description"],
        canonical=canonical,
        og_url=og_url,
        body_class=f'page-{meta.get("page", "inner")}',
        home_current=' aria-current="page"' if url_path == "/" else "",
        brand_mark=BRAND_MARK,
        nav="\n".join(nav_lines),
        body=body,
    )


def out_file(url_path: str) -> pathlib.Path:
    if url_path.endswith(".html"):
        return OUT / url_path.lstrip("/")
    return OUT / url_path.lstrip("/") / "index.html"


def main():
    pages = sorted((ROOT / "src" / "pages").glob("*.html"))
    sitemap = []
    for page in pages:
        meta, body = parse(page)
        target = out_file(meta["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(meta, body), encoding="utf-8")
        if meta["path"] != "/404.html":
            sitemap.append(meta["path"])
        print("wrote", target.relative_to(OUT))
    urls = "\n".join(f"  <url><loc>{DOMAIN}{p}</loc></url>" for p in sorted(sitemap))
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n</urlset>\n",
        encoding="utf-8",
    )
    print("wrote sitemap.xml")


if __name__ == "__main__":
    main()

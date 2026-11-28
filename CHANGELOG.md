# Changelog

All notable changes to this repository are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

- Repository created (November 2026).
- First draft of the company website (November 26, 2026): Home, What we do, Why it matters, Research and open source, About, Contact, Privacy and 404 pages; plain HTML and CSS with no JavaScript; security headers for Cloudflare Pages; `security.txt`. Not yet published.
- Simplified to a high-level version (November 26, 2026) while the business plan is in progress: shorter pages, no dates, licenses, tiers or business-model details; "Why it matters" trimmed to five sources.
- New visual design (November 26, 2026): self-hosted IBM Plex Sans Condensed and Source Serif 4; home-page diagram of traffic passing through the edge (plays once on load, static when reduced motion is requested); section layout with headings on the left; timeline on Why it matters; dark footer with the principal office address.
- Site published at https://sovereigninfralab.com through a Cloudflare Worker with static assets (November 26, 2026). Added `wrangler.jsonc` so missing pages show the site's 404 page and the deploy settings live in the repository.
- Turned off the `workers.dev` copy of the site and public Version URLs (November 28, 2026), so the site is served only at sovereigninfralab.com and www.
- Added `tools/check_site.py` and a GitHub Actions workflow that runs it on every pull request, push to `main` and weekly (November 28, 2026): checks that `site/` is rebuilt from `src/`, internal links, Content Security Policy fit, security headers and the `security.txt` expiry date. Dependabot keeps the pinned action up to date. `tools/diagram.py` now accepts an output path.

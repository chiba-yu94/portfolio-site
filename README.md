# Yutchi Apps

The public home for Yutchi's released macOS and iOS apps, with Japanese and English product pages, screenshots, usage notes, and support links.

Live site: [chiba-yu94.github.io/portfolio-site](https://chiba-yu94.github.io/portfolio-site/)

## Build and check

Use Python 3.9 or later. No third-party packages, JavaScript package manager, or backend are required.

```sh
python3 scripts/build.py
python3 scripts/check_site.py
site_preview_root=$(mktemp -d)
ln -s "$PWD" "$site_preview_root/portfolio-site"
python3 -m http.server 8000 --bind 127.0.0.1 --directory "$site_preview_root"
```

For that preview command, open `http://127.0.0.1:8000/portfolio-site/`. The temporary staging directory preserves the GitHub Pages project path without serving sibling projects. The server listens on loopback only. Stop it with Ctrl-C when finished.

The checker runs without network access. It verifies the bilingual catalog, generated page metadata, structured data, images and recorded asset hashes, internal links and anchors, preserved routes, sitemap, and robots file. It cannot confirm current App Store availability or visually evaluate layout; verify those separately before publishing.

## Project layout

| Path | Purpose |
|---|---|
| `data/products.json` | Central product facts and Japanese/English copy |
| `data/assets-manifest.json` | Public asset provenance and SHA-256 hashes |
| `scripts/build.py` | Generates crawlable HTML, sitemap, and robots file |
| `scripts/check_site.py` | Dependency-free static validation |
| `styles.css`, `site.js` | Shared responsive styling and progressive enhancement |
| `assets/` | Approved public icons, screenshots, and developer artwork |
| `en/` | Generated English pages; Japanese pages use the default routes |

Edit central data and the generator rather than individual generated pages. Keep generated HTML checked in: GitHub Pages serves the root of the `main` branch directly, with `.nojekyll` and no application server.

The existing `/support/`, `/privacy/`, and `/matanenote/` routes remain available. Product-specific support and policy URLs already used by apps remain unchanged. The support contact is [yutchi.apps@gmail.com](mailto:yutchi.apps@gmail.com).

See [maintenance instructions](docs/maintenance.md) for release verification, screenshots, translations, policy updates, publishing, and rollback.

See the [search discoverability review](docs/search-discoverability/README.md) for the SEO audit, Search Console setup, referral measurement plan, and unpublished File Transfer troubleshooting drafts.

Optional Search Console verification and consent-gated website measurement use `data/measurement.json`, `scripts/measurement.py`, and `analytics.js`. Analytics is disabled by default. See [measurement operations](docs/measurement.md) before changing IDs, consent behavior, campaigns, or deployment settings.

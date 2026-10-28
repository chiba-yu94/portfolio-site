#!/usr/bin/env python3
"""Check the generated site and its catalog without network access or dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree
from measurement import load_settings, campaign_url


SITE_URL = "https://chiba-yu94.github.io/portfolio-site/"
CONTACT = "yutchi.apps@gmail.com"
LANGUAGES = ("ja", "en")
LEGACY_ROUTES = ("support/", "privacy/", "matanenote/")
LOCALIZED_FIELDS = (
    "name", "summary", "features", "limits", "privacy", "problem", "audience",
    "faq", "support_note", "os", "languages", "price", "support_url", "privacy_url",
)
FORBIDDEN = re.compile(
    r"Release\s+Preflight|release-preflight|6820354098|Chiba\s*Apps|"
    r"PIXEL\s*NAPS|Behind[\s_-]*the[\s_-]*Specs", re.IGNORECASE
)


class Document(HTMLParser):
    def __init__(self, path: Path, raw: str):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.raw = raw
        self.lang = []
        self.title_count = 0
        self.title_parts = []
        self.in_title = False
        self.descriptions = []
        self.canonicals = []
        self.alternates = {}
        self.alternate_counts = Counter()
        self.tags = Counter()
        self.ids = Counter()
        self.references = []
        self.images = []
        self.json_ld = []
        self.json_buffer = None
        self.feed(raw)
        self.close()

    @property
    def title(self):
        return " ".join("".join(self.title_parts).split())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags[tag] += 1
        if tag == "html":
            self.lang.append(attrs.get("lang"))
        if tag == "title":
            self.title_count += 1
            self.in_title = True
        if attrs.get("id"):
            self.ids[attrs["id"]] += 1
        if tag == "a" and attrs.get("name"):
            self.ids[attrs["name"]] += 1
        if tag == "meta" and attrs.get("name", "").lower() == "description":
            self.descriptions.append(attrs.get("content", ""))
        if tag == "link":
            rel = attrs.get("rel", "").lower().split()
            if "canonical" in rel:
                self.canonicals.append(attrs.get("href", ""))
            if "alternate" in rel and "hreflang" in attrs:
                lang = attrs["hreflang"]
                self.alternate_counts[lang] += 1
                self.alternates[lang] = attrs.get("href", "")
        if tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self.json_buffer = []
        if tag == "img":
            self.images.append(attrs)
        for key in ("href", "src"):
            if key in attrs:
                self.references.append((tag, key, attrs[key]))
        if "srcset" in attrs:
            self.references.extend((tag, "srcset", entry.strip().split()[0])
                                   for entry in attrs["srcset"].split(",") if entry.strip())

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "script" and self.json_buffer is not None:
            self.json_ld.append("".join(self.json_buffer))
            self.json_buffer = None

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)
        if self.json_buffer is not None:
            self.json_buffer.append(data)


def image_size(path: Path):
    """Read PNG/JPEG/GIF dimensions without loading or changing image pixels."""
    with path.open("rb") as stream:
        header = stream.read(24)
        if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
            return struct.unpack(">II", header[16:24])
        if header[:6] in (b"GIF87a", b"GIF89a"):
            return struct.unpack("<HH", header[6:10])
        if header[:2] != b"\xff\xd8":
            raise ValueError("unsupported image format; use PNG, JPEG, or GIF")
        stream.seek(2)
        while True:
            marker = stream.read(1)
            if not marker:
                break
            if marker != b"\xff":
                continue
            while marker == b"\xff":
                marker = stream.read(1)
            if not marker:
                break
            code = marker[0]
            if code in (0xD8, 0xD9, 0x01) or 0xD0 <= code <= 0xD7:
                continue
            length_bytes = stream.read(2)
            if len(length_bytes) != 2:
                break
            length = struct.unpack(">H", length_bytes)[0]
            if length < 2:
                break
            if code in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                        0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                dimensions = stream.read(5)
                if len(dimensions) == 5:
                    height, width = struct.unpack(">HH", dimensions[1:5])
                    return width, height
                break
            stream.seek(length - 2, 1)
    raise ValueError("could not read image dimensions")


def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


def populated(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value) and all(populated(item) for item in value)
    return False


class Checker:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.errors = []
        self.pages = {}
        self.manifest_paths = set()
        self.external_policy_urls = set()
        self.products = []
        self.used_images = set()
        self.base = urlsplit(SITE_URL)

    def expect(self, condition, message):
        if not condition:
            self.errors.append(message)
        return bool(condition)

    def read_json(self, relative):
        try:
            return json.loads((self.root / relative).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            self.errors.append(f"{relative}: cannot read valid JSON ({exc})")
            return None

    def local_file(self, relative):
        target = (self.root / relative).resolve()
        if not target.is_relative_to(self.root):
            raise ValueError("path escapes the site root")
        return target

    def check_catalog(self):
        catalog = self.read_json("data/products.json")
        if not isinstance(catalog, dict):
            return
        self.expect(catalog.get("brand") == "Yutchi Apps", "catalog: expected Yutchi Apps brand")
        self.expect(catalog.get("contact") == CONTACT, "catalog: incorrect public support contact")
        self.products = catalog.get("products", [])
        if not self.expect(isinstance(self.products, list) and self.products, "catalog: products must be a nonempty list"):
            self.products = []
            return
        ids = []
        stores = []
        for product in self.products:
            if not isinstance(product, dict):
                self.errors.append("catalog: each product must be an object")
                continue
            label = product.get("id", "<missing id>")
            ids.append(label)
            self.expect(bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", label)), f"{label}: invalid product id")
            self.expect(not FORBIDDEN.search(json.dumps(product, ensure_ascii=False)), f"{label}: unreleased or unrelated product content")
            self.expect(product.get("release_status") == "released", f"{label}: only verified released products belong in the catalog")
            for key in ("store_name", "platform", "version", "category", "currency"):
                self.expect(populated(product.get(key)), f"{label}: missing {key}")
            try:
                verified = date.fromisoformat(product["verified_date"])
                self.expect(verified <= date.today(), f"{label}: verified_date is in the future")
            except (KeyError, TypeError, ValueError):
                self.errors.append(f"{label}: verified_date must be an ISO calendar date")
            for key in LOCALIZED_FIELDS:
                translated = product.get(key)
                valid = isinstance(translated, dict) and all(populated(translated.get(lang)) for lang in LANGUAGES)
                self.expect(valid, f"{label}: {key} needs nonempty Japanese and English values")
                if valid and key in ("features", "limits", "faq"):
                    self.expect(all(isinstance(translated[lang], list) for lang in LANGUAGES), f"{label}: {key} must contain localized lists")
                if key in ("support_url", "privacy_url") and valid:
                    for address in translated.values():
                        self.expect(urlsplit(address).scheme == "https", f"{label}: {key} must use HTTPS")
                        self.external_policy_urls.add(address)
            for lang in LANGUAGES:
                for pair in product.get("faq", {}).get(lang, []):
                    self.expect(isinstance(pair, list) and len(pair) == 2 and all(populated(x) for x in pair), f"{label}: {lang} FAQ needs question/answer pairs")
            address = product.get("store_url", "")
            stores.append(address)
            parsed = urlsplit(address)
            match = re.search(r"/id(\d+)(?:/|$)", parsed.path)
            self.expect(parsed.scheme == "https" and parsed.netloc == "apps.apple.com" and bool(match), f"{label}: invalid public App Store URL")
            available = product.get("availability", {})
            self.expect(isinstance(available, dict) and any(v is True for v in available.values()), f"{label}: no verified available region")
            urls = product.get("store_urls", {})
            self.expect(isinstance(urls, dict) and bool(urls), f"{label}: regional store_urls missing")
            for region, regional in urls.items():
                self.expect(available.get(region) is True, f"{label}: store URL is not marked available in {region}")
                region_url = urlsplit(regional)
                self.expect(region_url.netloc == "apps.apple.com" and region_url.scheme == "https" and region_url.path.startswith(f"/{region}/") and bool(match) and f"/id{match[1]}" in region_url.path, f"{label}: inconsistent {region} store URL")
            prices = product.get("prices", {})
            self.expect(isinstance(prices, dict) and bool(prices), f"{label}: verified regional prices missing")
            if isinstance(prices, dict):
                for region, price in prices.items():
                    valid_price = isinstance(price, dict) and isinstance(price.get("price"), (int, float)) and not isinstance(price.get("price"), bool) and price["price"] >= 0
                    self.expect(valid_price and bool(re.fullmatch(r"[A-Z]{3}", price.get("currency", ""))), f"{label}: invalid regional price in {region}")
                    self.expect(available.get(region) is True, f"{label}: price for unverified region {region}")
            sources = product.get("source_urls", [])
            self.expect(isinstance(sources, list) and any(isinstance(source, str) and source.startswith("https://itunes.apple.com/lookup?") and match and f"id={match[1]}" in source for source in sources), f"{label}: public Apple verification source missing")
            self.expect(isinstance(product.get("schema_price"), (float, int)) and not isinstance(product.get("schema_price"), bool) and product["schema_price"] >= 0, f"{label}: invalid schema_price")
            screenshots = product.get("screenshots", [])
            self.expect(isinstance(screenshots, list) and bool(screenshots), f"{label}: screenshots missing")
            for shot in screenshots:
                if not isinstance(shot, dict):
                    self.errors.append(f"{label}: invalid screenshot record")
                    continue
                self.expect(all(isinstance(shot.get(key), int) and shot[key] > 0 for key in ("width", "height")), f"{label}: screenshot dimensions must be positive integers")
                self.expect(isinstance(shot.get("alt"), dict) and all(populated(shot["alt"].get(lang)) for lang in LANGUAGES), f"{label}: screenshot alt text needs both languages")
                try:
                    path = self.local_file(shot["src"])
                    size = image_size(path)
                    self.expect(size == (shot.get("width"), shot.get("height")), f"{label}: screenshot dimensions differ from {shot['src']}")
                except (KeyError, OSError, ValueError) as exc:
                    self.errors.append(f"{label}: invalid screenshot file ({exc})")
        self.expect(len(ids) == len(set(ids)), "catalog: duplicate product ids")
        self.expect(len(stores) == len(set(stores)), "catalog: duplicate public store URLs")

    def check_manifest(self):
        manifest = self.read_json("data/assets-manifest.json")
        if not self.expect(isinstance(manifest, list) and bool(manifest), "asset manifest must be a nonempty list"):
            return
        for entry in manifest:
            if not isinstance(entry, dict):
                self.errors.append("asset manifest: entry must be an object")
                continue
            relative = entry.get("path", "")
            self.expect(relative not in self.manifest_paths, f"asset manifest: duplicate {relative}")
            self.manifest_paths.add(relative)
            digest = entry.get("sha256", "")
            self.expect(bool(re.fullmatch(r"[a-f0-9]{64}", digest)), f"asset manifest: invalid SHA-256 for {relative}")
            source = entry.get("source_url")
            public_source = isinstance(source, str) and urlsplit(source).scheme == "https" and bool(urlsplit(source).netloc)
            generated_source = source is None and populated(entry.get("provenance"))
            self.expect(public_source or generated_source, f"asset manifest: public source URL or accurate generated-artwork provenance required for {relative}")
            try:
                path = self.local_file(relative)
                self.expect(hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"asset manifest: hash mismatch for {relative}")
            except (OSError, ValueError) as exc:
                self.errors.append(f"asset manifest: {relative} cannot be verified ({exc})")

    def discover_pages(self):
        for path in sorted(self.root.rglob("index.html")):
            relative = path.relative_to(self.root)
            if any(part.startswith(".") for part in relative.parts) or relative.parts[0] in ("assets", "data", "docs", "scripts"):
                continue
            try:
                doc = Document(path, path.read_text(encoding="utf-8"))
                self.pages[path.resolve()] = doc
            except (OSError, ValueError) as exc:
                self.errors.append(f"{relative}: cannot parse HTML ({exc})")
        self.expect(bool(self.pages), "no generated index.html pages found; run scripts/build.py")
        for route in ("", *LEGACY_ROUTES):
            self.expect((self.root / route / "index.html").resolve() in self.pages, f"legacy route missing: /{route}")

    def canonical_for(self, doc):
        relative = doc.path.parent.relative_to(self.root).as_posix()
        route = "" if relative == "." else relative + "/"
        return SITE_URL + route, route

    def resolve_reference(self, source, reference):
        absolute = urljoin(source, reference)
        parsed = urlsplit(absolute)
        if parsed.netloc != self.base.netloc:
            return None, parsed.fragment
        decoded = unquote(parsed.path)
        if not decoded.startswith(self.base.path):
            self.expect(absolute.split("#", 1)[0] in self.external_policy_urls, f"unexpected same-origin URL outside the site: {absolute}")
            return None, parsed.fragment
        relative = decoded[len(self.base.path):]
        target = self.local_file(relative)
        if parsed.path.endswith("/") or target.is_dir():
            target /= "index.html"
        return target, unquote(parsed.fragment)

    def check_json_ld(self, doc, label):
        self.expect(bool(doc.json_ld), f"{label}: JSON-LD missing")
        product = None
        _, route = self.canonical_for(doc)
        plain_route = route.removeprefix("en/")
        region = "us" if route.startswith("en/") else "jp"
        for item in self.products:
            expected = "matanenote/" if item.get("id") == "matanenote" else f"apps/{item.get('id')}/"
            if plain_route == expected:
                product = item
                break
        applications = []
        for script in doc.json_ld:
            try:
                data = json.loads(script)
            except ValueError as exc:
                self.errors.append(f"{label}: invalid JSON-LD ({exc})")
                continue
            self.expect(isinstance(data, dict) and data.get("@context") == "https://schema.org", f"{label}: JSON-LD needs the schema.org context")
            for obj in objects(data):
                self.expect("aggregateRating" not in obj and "review" not in obj, f"{label}: unverified rating/review structured data")
                kind = obj.get("@type")
                kinds = kind if isinstance(kind, list) else [kind]
                if "SoftwareApplication" in kinds:
                    applications.append(obj)
                    self.expect(product is not None, f"{label}: SoftwareApplication on a non-product page")
                    if product:
                        store_urls = product.get("store_urls", {})
                        store_url = store_urls.get(region, store_urls.get("jp"))
                        prices = product.get("prices", {})
                        regional_price = prices.get(region, prices.get("jp", {}))
                        page_lang = "en" if route.startswith("en/") else "ja"
                        for key, expected in (("name", product.get("store_name")), ("downloadUrl", store_url), ("softwareVersion", product.get("version")), ("applicationCategory", product.get("category")), ("url", self.canonical_for(doc)[0]), ("operatingSystem", product.get("os", {}).get(page_lang))):
                            self.expect(obj.get(key) == expected, f"{label}: SoftwareApplication {key} differs from verified catalog")
                        offer = obj.get("offers", {})
                        self.expect(isinstance(offer, dict) and offer.get("price") == regional_price.get("price") and offer.get("priceCurrency") == regional_price.get("currency") and offer.get("url") == store_url, f"{label}: offer differs from verified regional catalog")
        if product:
            self.expect(len(applications) == 1, f"{label}: expected exactly one verified SoftwareApplication")

    def check_pages(self):
        titles = {}
        for doc in self.pages.values():
            label = doc.path.relative_to(self.root).as_posix()
            canonical, route = self.canonical_for(doc)
            lang = "en" if route.startswith("en/") else "ja"
            plain = route.removeprefix("en/")
            self.expect(doc.lang == [lang], f"{label}: html lang must be {lang}")
            self.expect(doc.title_count == 1 and bool(doc.title), f"{label}: one nonempty title required")
            self.expect(doc.title not in titles, f"{label}: duplicate title also used by {titles.get(doc.title)}")
            titles[doc.title] = label
            self.expect(len(doc.descriptions) == 1 and bool(doc.descriptions[0].strip()), f"{label}: one nonempty meta description required")
            self.expect(doc.canonicals == [canonical], f"{label}: canonical must be {canonical}")
            for alternate, expected in (("ja", SITE_URL + plain), ("en", SITE_URL + "en/" + plain), ("x-default", SITE_URL + plain)):
                self.expect(doc.alternate_counts[alternate] == 1 and doc.alternates.get(alternate) == expected, f"{label}: invalid {alternate} hreflang")
                try:
                    target, _ = self.resolve_reference(canonical, expected)
                    self.expect(target in self.pages, f"{label}: hreflang target is missing: {expected}")
                except ValueError as exc:
                    self.errors.append(f"{label}: invalid hreflang path ({exc})")
            self.expect(doc.tags["h1"] == 1, f"{label}: exactly one h1 required")
            self.expect(doc.tags["main"] == 1, f"{label}: exactly one semantic main required")
            self.expect(all(count == 1 for count in doc.ids.values()), f"{label}: duplicate HTML ids/named anchors")
            self.expect(not FORBIDDEN.search(doc.raw), f"{label}: unreleased or unrelated brand/product content")
            email_addresses = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", doc.raw)
            self.expect(all(address == CONTACT for address in email_addresses), f"{label}: unexpected public email address")
            self.check_json_ld(doc, label)
            for tag, attribute, reference in doc.references:
                parsed = urlsplit(reference)
                if parsed.scheme == "mailto":
                    self.expect(unquote(parsed.path) == CONTACT, f"{label}: mailto must use the public support contact")
                    continue
                if parsed.scheme and parsed.scheme not in ("https", "http"):
                    self.errors.append(f"{label}: unsupported {attribute} URL scheme: {parsed.scheme}")
                    continue
                self.expect(bool(reference.strip()), f"{label}: empty {tag} {attribute}")
                try:
                    target, anchor = self.resolve_reference(canonical, reference)
                    if target is not None:
                        self.expect(target.is_file(), f"{label}: missing local {attribute}: {reference}")
                        if anchor:
                            linked_doc = self.pages.get(target.resolve())
                            self.expect(linked_doc is not None and anchor in linked_doc.ids, f"{label}: missing anchor: {reference}")
                except ValueError as exc:
                    self.errors.append(f"{label}: invalid reference {reference!r} ({exc})")
            for image in doc.images:
                self.expect("alt" in image, f"{label}: image alt attribute missing")
                try:
                    width, height = int(image.get("width", "0")), int(image.get("height", "0"))
                    self.expect(width > 0 and height > 0, f"{label}: positive image width and height required")
                    path, _ = self.resolve_reference(canonical, image.get("src", ""))
                    if path is not None and path.is_file():
                        actual_width, actual_height = image_size(path)
                        self.expect(width * actual_height == height * actual_width, f"{label}: distorted image aspect ratio: {image.get('src')}")
                        self.used_images.add(path.relative_to(self.root).as_posix())
                except (OSError, TypeError, ValueError) as exc:
                    self.errors.append(f"{label}: invalid image dimensions ({exc})")
        for path in self.used_images:
            self.expect(path in self.manifest_paths, f"rendered image missing from asset manifest: {path}")

    def check_search_files(self):
        expected = {self.canonical_for(doc)[0] for doc in self.pages.values()}
        try:
            xml = ElementTree.parse(self.root / "sitemap.xml")
            namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            urls = [node.text for node in xml.findall("s:url/s:loc", namespace)]
            self.expect(len(urls) == len(set(urls)), "sitemap: duplicate URLs")
            self.expect(set(urls) == expected, "sitemap: URLs must match every generated canonical exactly")
        except (OSError, ElementTree.ParseError) as exc:
            self.errors.append(f"sitemap.xml: cannot parse sitemap ({exc})")
        try:
            robots = (self.root / "robots.txt").read_text(encoding="utf-8")
            self.expect(f"Sitemap: {SITE_URL}sitemap.xml" in robots, "robots.txt: canonical sitemap missing")
            self.expect(bool(re.search(r"^User-agent:\s*\*\s*$", robots, re.MULTILINE)), "robots.txt: general crawler group missing")
            self.expect(not re.search(r"^Disallow:\s*/\s*$", robots, re.MULTILINE), "robots.txt: site-wide crawl block")
        except OSError as exc:
            self.errors.append(f"robots.txt: cannot read file ({exc})")
        self.expect((self.root / ".nojekyll").is_file(), ".nojekyll missing for GitHub Pages")

    def check_measurement(self):
        try:
            settings = load_settings(self.root, self.products)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.errors.append(f"measurement configuration: {exc}")
            return
        expected_urls = sorted({campaign_url(settings, p, region) for p in self.products for region in p['store_urls']})
        for doc in self.pages.values():
            canonical, _ = self.canonical_for(doc)
            configs = re.findall(r'<script id="site-measurement-config" type="application/json">(.*?)</script>', doc.raw, re.DOTALL)
            self.expect(len(configs) == 1, f"{doc.path}: exactly one measurement configuration required")
            self.expect(doc.raw.count('src="/portfolio-site/analytics.js"') == 1, f"{doc.path}: exactly one local consent runtime required")
            self.expect(doc.raw.count('data-analytics-settings') == 1, f"{doc.path}: one accessible consent settings entry required")
            self.expect(doc.raw.count('<meta name="referrer" content="origin">') == 1, f"{doc.path}: origin-only referrer policy required")
            self.expect(not re.search(r'<script[^>]+src=[\"\'][^\"\']*(?:googletagmanager|google-analytics|connect\.facebook)', doc.raw), f"{doc.path}: third-party tag must not load outside the consent runtime")
            self.expect('fbq(' not in doc.raw and 'gtag(' not in doc.raw, f"{doc.path}: unexpected inline tracking command")
            verification = re.findall(r'<meta name="google-site-verification" content="([^"]+)">', doc.raw)
            expected_token = [settings['google_site_verification']] if canonical == SITE_URL and settings['google_site_verification'] else []
            self.expect(verification == expected_token, f"{doc.path}: Google verification token does not match settings")
            try:
                config = json.loads(configs[0])
                self.expect(config['canonical_url'] == canonical and config['page_title'] == doc.title, f"{doc.path}: fixed measurement page metadata mismatch")
                self.expect(config['language'] == doc.lang[0], f"{doc.path}: measurement language mismatch")
                self.expect(all(config.get(k) == v for k, v in settings['analytics'].items()), f"{doc.path}: stale analytics switches/ID")
                page_store_links = {urljoin(canonical, href) for href in re.findall(r'\bhref="([^"]+)"', doc.raw)}
                from html import unescape
                page_store_links = {unescape(href) for href in page_store_links}
                self.expect(config['app_store_urls'] == sorted(set(expected_urls) & page_store_links), f"{doc.path}: unapproved App Store measurement URL")
                self.expect('main' in config['allowed_hashes'] and set(config['allowed_hashes']).issubset(doc.ids), f"{doc.path}: unknown measurement fragment allowlist")
            except (IndexError, ValueError, KeyError, TypeError) as exc:
                self.errors.append(f"{doc.path}: malformed measurement config ({exc})")
        for lang in ('', 'en/'):
            path = self.root / lang / 'privacy-policies/index.html'
            self.expect('id="website-privacy"' in path.read_text(encoding='utf-8'), f"{path}: website-specific privacy notice missing")

    def run(self):
        self.check_catalog()
        self.check_manifest()
        self.discover_pages()
        self.check_pages()
        self.check_search_files()
        self.check_measurement()
        return self.errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="site repository root")
    args = parser.parse_args()
    checker = Checker(args.root)
    errors = checker.run()
    if errors:
        print(f"FAIL: {len(errors)} static checks failed.", file=sys.stderr)
        for message in errors:
            print(f"- {message}", file=sys.stderr)
        return 1
    print(f"PASS: {len(checker.pages)} pages, {len(checker.products)} released apps, "
          f"{len(checker.manifest_paths)} asset hashes, internal links and anchors, "
          "bilingual metadata, structured data, search files, and consent-gated measurement configuration.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Maintaining Yutchi Apps

## Update product information

Edit `data/products.json`, then run the generator and checker from the repository root:

```sh
python3 scripts/build.py
python3 scripts/check_site.py
git diff --check
```

Keep every required localized field complete in both `ja` and `en`: names, summaries, features, limitations, privacy descriptions, audience and problem statements, FAQs, support notes, OS requirements, languages, pricing text, and screenshot alternative text. Product names may legitimately match across languages. English copy should accurately explain Japan-only availability where applicable.

Regional `store_urls`, `availability`, and `prices` must agree with verified Apple information. Japanese pages use Japan's listing and currency. English pages use the US listing when available, otherwise the verified Japanese listing. Do not imply worldwide distribution from one available region.

Do not edit generated `index.html` files as the source of a change; the next build would overwrite those edits. Shared page structure belongs in `scripts/build.py`; visual changes belong in `styles.css`, and optional interactions belong in `site.js`.

## Add an app or confirm a release

1. Confirm the app is publicly available on its actual App Store page and Apple's public lookup response. An accepted build, review submission, or approval email alone is insufficient.
2. Verify its name, public version, supported devices and OS, regions, pricing and purchase model, capabilities, limitations, and privacy characteristics. Record the verification date and public source URLs in the catalog.
3. Add a complete product object with a unique stable `id`, both language versions, regional store URLs and prices, and approved assets. Use the existing product records as the schema reference.
4. Add the app's original support and privacy URLs. Keep URLs already embedded in released apps valid; changing this website does not change Apple metadata or an app binary.
5. Build, run the checker, and visually review both language versions on desktop and mobile before publishing.

Only verified released apps belong in the public catalog. Release Preflight currently has an explicit exclusion guard in the checker. After a future public release is independently confirmed, review that guard deliberately together with the new catalog entry. Do not remove it merely to make an unverified entry pass.

Never invent reviews, ratings, awards, download counts, or security guarantees. SoftwareApplication structured data must reflect the verified regional product record. Do not add aggregate ratings or review markup without a separately authorized, verifiable source and an explicit review of the checker rules.

## Replace icons or screenshots

Reuse approved public App Store assets when possible. Use images that match the public version, and avoid customer notes, private filenames, credentials, unrelated brands, or unpublished app screens.

- Save website assets under `assets/` with stable, descriptive names.
- Add or update their entries in `data/assets-manifest.json`, including public source URLs or an accurate generated-artwork provenance note and the SHA-256 of the exact committed file.
- For screenshots, set the actual pixel width and height in the catalog, and provide useful Japanese and English alt text. Decorative repeated icons may use an empty HTML alt attribute when their name appears next to them.
- Preserve aspect ratios. PNG, JPEG, and GIF dimensions are supported by the dependency-free checker.
- Keep original generation prompts and private audit material outside this public repository. Include only approved public artwork and appropriate provenance here.

Compute a file's SHA-256 using Python's standard library:

```sh
python3 -c 'import hashlib,pathlib; p=pathlib.Path("assets/example.png"); print(hashlib.sha256(p.read_bytes()).hexdigest())'
```

Changing a file without updating its recorded hash intentionally fails validation. Do not update a hash merely to silence a failure without checking the replacement asset.

## Support and privacy policies

The public support contact is `yutchi.apps@gmail.com`. A contact change should update the central catalog contact and generator constant together, then regenerate every language page. Mail links are normal `mailto:` links; there is no contact form, visitor account system, or backend. Optional website measurement is controlled separately through `data/measurement.json`, requires explicit activation approval and the [measurement review and validation procedure](measurement.md). Do not infer application analytics from this website setting.

Keep each product's existing support and privacy URL intact. Some policies live in separate public support repositories; a link from this site is not a replacement of those original documents. Coordinate any separate support-site contact change with that repository's deployment.

Preserve the original meaning, established date, provider identity, and product-specific data-handling statements of an existing policy. A support-address-only update should say that the contact changed, identify the change date, and leave the substantive clauses unchanged. Do not turn different apps' policies into a generic promise. Review both language versions against the original policy and keep translations labeled where appropriate.

Use Git history to retain a reviewable record of changes. Do not rewrite historical versions, legal identities, authentication addresses, or unrelated personal contact details as part of a public support migration. Never commit credentials, private paths, raw audit exports, customer data, or private repository files.

## Validate generated output

The static checker covers:

- Unique titles, HTML language, canonical URL, meta description, and reciprocal Japanese/English/default hreflang targets for every generated page.
- One H1 and semantic main, unique anchors, image alt attributes and dimensions, and undistorted image aspect ratios.
- Every local href, src, and srcset file and named anchor. Existing app-specific policy/support links on other project paths are treated as declared external destinations, not files in this site.
- Valid JSON-LD, product metadata and regional offers matching the catalog, and no unverified aggregate rating or review markup.
- Complete required catalog translations, released status, valid Apple URLs and verification sources, and exclusion of the unreleased product and unrelated brands.
- Sitemap coverage, robots sitemap declaration, `.nojekyll`, asset-manifest hashes, and manifest coverage of rendered images.

This is a local consistency check, not live release verification, a complete accessibility audit, or a legal review. Also inspect keyboard navigation, image loading, narrow layouts, language switching, filters without JavaScript, and the actual public support links. No external service is contacted by the checker.

After changing the generator, build twice and compare the generated output to confirm reproducibility. Review the actual diff, including generated pages and metadata. Check that no stale pages, unverified app entries, or unintended routes were introduced.

## Publish and roll back

GitHub Pages serves the repository root on `main`; the public project path is `/portfolio-site/`. Keep `.nojekyll` in place. Do not upload app source code or production builds. The website requires no environment secrets or server-side process.

Before merging a prepared change, require a clean static check, review the generated diff, and complete visual QA. After the authorized merge or push to `main`, check the GitHub Pages deployment result and the live default-language and English pages. Confirm that `/support/`, `/privacy/`, and `/matanenote/` still resolve and the new contact appears where intended.

For a faulty deployment, revert the specific website commit on `main` and let Pages redeploy. Preserve unrelated work and history; avoid force pushes or deleting legacy routes. Verify the restored live pages, then prepare the correction on a separate branch and repeat the checks. Site rollback does not roll back an app release, App Store metadata, or another support repository.

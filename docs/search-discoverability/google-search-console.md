# Google Search Console setup

Prepared 2026-10-27. Instructions only: no property, verification token, or sitemap submission was created during this audit.

## Property and ownership

1. Sign in to [Search Console](https://search.google.com/search-console/) with the Google account intended to retain ownership. Check for an existing property before adding one.
2. Add a **URL-prefix** property with exactly `https://chiba-yu94.github.io/portfolio-site/`. It includes the Japanese and English pages under that path. A Domain property requires DNS verification; this project does not control DNS for `github.io`.
3. Prefer **HTML file** verification if offered. Download Google's actual file and preserve its name and contents. Place it at the repository root only if this produces the exact public URL specified by the wizard, normally inside `/portfolio-site/`. Never invent a verification token.
4. Prepare a reviewed change, run the existing checker, and obtain deployment approval. After approved deployment, confirm the wizard's URL is publicly accessible with the exact content; then select **Verify**. Keep the file after verification and out of the page sitemap.
5. If the required file location cannot be served, use **HTML tag** verification instead. Insert Google's exact tag into the home page `<head>` through `shell()` in `scripts/build.py`, regenerate, review, and obtain deployment approval. Editing generated HTML alone would lose the tag on the next build. Keep existing owners' verification tokens.

The current repository and public HTML contain no observed Google verification file/tag. This does **not** prove the property is unverified: another method or an existing owner may already provide access. See Google's [property types](https://support.google.com/webmasters/answer/34592?hl=en) and [ownership verification](https://support.google.com/webmasters/answer/9008080?hl=en).

## Sitemap and indexing

In the verified property's **Sitemaps** report, submit:

`https://chiba-yu94.github.io/portfolio-site/sitemap.xml`

Confirm successful processing and inspect any errors. The current sitemap lists 20 canonical pages. `/portfolio-site/robots.txt` is served, but crawler rules belong at the host root; `/robots.txt` currently returns 404. Direct sitemap submission avoids relying on the project-level robots file for discovery. No new repository, domain, or analytics service is needed. Sources: [sitemaps](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap), [robots location](https://developers.google.com/crawling/docs/robots-txt/create-robots-txt).

Use **URL Inspection** for the home page and `/en/apps/file-transfer-preflight/`. Compare the indexed status and Google-selected canonical with the intended URL. Use a live test to diagnose access; request indexing if appropriate. An accessible page or successful live test does not guarantee indexing. [URL Inspection documentation](https://support.google.com/webmasters/answer/9012289?hl=en).

## Measurement baseline

Export an initial Performance report when data is available. Compare matching date ranges using Pages and Queries, separating the English File Transfer page from the whole site. Record impressions, clicks, CTR, and average position. These measure Google Search exposure and visits to this website; they do not measure App Store purchases or website-to-store clicks. [Performance report](https://support.google.com/webmasters/answer/7576553?hl=en).

The sibling support projects are outside this URL prefix. Add their own URL-prefix properties only if separate search diagnostics are needed; preserve their existing URLs.

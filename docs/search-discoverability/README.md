# Search discoverability review

Audit date: 2026-10-27. Baseline: `c5a6b4a` on `main`.

This is the pre-integration audit snapshot. See [measurement operations](../measurement.md) for the later, disabled-by-default consent integration and its current activation requirements.

This folder contains review material only. No generated page, product data, application source, account setting, or deployed site was changed. The two troubleshooting guides are drafts; they are not new public routes or sitemap entries.

## Current technical findings

- All 20 sitemap pages return HTTP 200, with unique titles, descriptions, self-referencing canonicals, Japanese/English/default alternates, and one H1 each.
- Open Graph and JSON-LD are present. The existing checker passes for 20 pages, four released products, 17 asset hashes, internal links, bilingual metadata, and structured data. This is not a Google rich-result eligibility or ranking guarantee.
- No `noindex` was observed in HTML or HTTP headers. Search Console access, Google indexing, and search performance were not inspected in an authenticated account.
- The project robots file returns 200; the host-root robots file returns 404. The project file does not establish host-wide crawler policy. Submit the existing sitemap directly through Search Console instead of creating infrastructure to move robots.txt.
- A missing host-root robots file is not evidence of a crawl block. No blocking directive was observed; Google indexing remains unverified.
- No Google verification tag or file was observed in the audited source. Existing verification through another method remains unknown.

## Review order

1. Follow [Search Console setup](google-search-console.md), checking for an existing property first. Publishing a verification file/tag requires approval.
2. Review [referral measurement](referral-measurement.md). Obtain real Apple-generated campaign links before proposing link changes. No analytics code is needed for this first measurement step.
3. Review the [File Transfer content gaps](content-gaps.md) and the two drafts: [filename/path troubleshooting](file-transfer-filename-path-guide.md) and [case/Unicode collisions](file-transfer-name-collision-guide.md).
4. After editorial approval, reuse the existing English product and support pages for useful guide sections and contextual links. Change the generator/data as appropriate, not generated HTML alone. Do not create near-duplicate landing pages. These are English-only drafts; do not present them as translated Japanese guides.
5. Review the sibling support site's missing portfolio return links described in the referral audit. Keep every existing support/privacy route and legal statement intact.

No approval or deployment is requested by this documentation change itself. A future public content, verification, navigation, or tracking change needs explicit approval, normal static checks, and review of the actual diff.

## Validation for a future implementation

Run `python3 scripts/build.py`, `python3 scripts/check_site.py`, and `git diff --check`. Check the affected English product/support sections, language behavior, keyboard navigation, and mobile layout. Verify App Store IDs, storefronts, campaign parameters, and destination URLs without generating test purchases or artificial downloads. Review whether any new measurement script changes privacy disclosures before adding it.

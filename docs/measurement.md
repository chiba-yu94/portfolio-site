# Website measurement operations

Prepared 2026-10-27. No deployment or live analytics validation has occurred. `data/measurement.json` is the only configuration source. Analytics defaults to **disabled**; empty IDs are intentional and must not be replaced with examples.

## Search Console

Use `yutchi.apps@gmail.com` and the exact URL-prefix property `https://chiba-yu94.github.io/portfolio-site/`. Check the property selector before creating another property. The real HTML-tag token obtained from Google is stored as `google_site_verification`; the generator renders it on the Japanese root homepage. Rebuilds preserve it. It is public verification metadata, not a login credential.

After an approved deployment, inspect the live homepage source, then use Google's Verify button. Only after successful verification, submit `https://chiba-yu94.github.io/portfolio-site/sitemap.xml` and inspect its processing status. Use URL Inspection for the homepage and English File Transfer page, recording indexed status separately from live accessibility. Do not claim indexing from sitemap submission. The project robots file is not host-root policy; do not edit github.io host files. See [setup details](search-discoverability/google-search-console.md) and [Google ownership instructions](https://support.google.com/webmasters/answer/9008080?hl=en).

## GA4 account prerequisites

Reuse a matching property if one already exists. Otherwise prepare account/property **Yutchi Apps**, web stream **Yutchi Apps Website**, and the existing website URL. Use Japan reporting time and JPY reporting currency; these do not change App Store prices. The owner must review Google's actual terms and data processing agreement before accepting them.

Before setting `account_settings_reviewed` to true, inspect the real administration interface and record:

- The actual `G-` Measurement ID from the web stream; no example or invented IDs.
- Optional account data sharing OFF; no Ads/product advertising links, Google Signals, user-provided data collection, advertising personalization, or remarketing activation.
- **All Enhanced Measurement OFF**, including outbound clicks and history-based pageviews. This prevents duplicate click events and uncontrolled link/query collection. Automatic base GA4 events may still exist.
- Email/query data redaction enabled as a supplementary safeguard; it is not the site's primary privacy boundary.
- User/event retention at the shortest suitable offered period (normally two months), activity-based retention reset OFF, and unnecessary granular location/device collection OFF. Retention settings do not delete every standard aggregate report on that schedule.

Then enter the real ID, keeping `enabled:false` until approval and validation. Account creation, settings review, a saved configuration, and live collection are separate completion states. See [Google privacy controls](https://developers.google.com/tag-platform/security/guides/privacy), [consent](https://developers.google.com/tag-platform/security/guides/consent), and [data redaction](https://support.google.com/analytics/answer/13544947?hl=en).

## Consent and payload boundaries

The local `analytics.js` creates a compact Japanese/English Accept/Reject panel only when configuration and origin are valid. Google code is absent until opt-in; rejected, missing, expired, invalid, or unavailable preferences do not load it. Only the scoped choice/version/expiry is saved in localStorage, for up to 180 days. The footer reopens settings. Withdrawal disables collection before clearing this integration's host-only, `/portfolio-site/` cookies and reloading without the Google tag. Cross-tab withdrawal is handled. Previously sent or already-started requests cannot be recalled.

The Google tag is restricted to the production origin and generated pathname. Any query string or undeclared fragment disables measurement; this intentionally excludes UTM-bearing visits instead of risking private parameters. Only the fixed canonical URL/title and referring origin are configured. The site sends an origin-only HTTP Referrer header; the tag loader requests no referrer. Advertising consent stays denied, ad data redaction is enabled, and URL passthrough is disabled. No email, link text, user ID, application content, or arbitrary URL is supplied by this integration.

Google still processes network/browser/device information and analytics identifiers after consent. Do not describe GA4 as completely anonymous or as sending no IP address. Website-specific disclosure is generated in Japanese and English at `/privacy-policies/#website-privacy`. Application policies and application behavior remain distinct and unchanged. Applicable regional obligations and international processing arrangements require the owner's review; this implementation is not legal certification.

## App Store clicks and Apple campaign links

Enhanced Measurement's general outbound collector exposes fields such as `link_url`; page-location overrides do not sanitize every other field. To meet the stricter scope here, it stays OFF. A small fallback emits the standard event name `click` with only `link_url`, `link_domain:'apps.apple.com'`, and `outbound:true`, after consent and tag initialization. The URL must exactly match a verified link rendered on that page, belong to one of the four released products, and have no unapproved parameters. Other links, mail links, arbitrary query values, and internal navigation receive no custom events. See Google's [outbound collection](https://support.google.com/analytics/answer/13566436?hl=en).

In GA4, filter `click` by `link_domain=apps.apple.com` and `outbound=true`; use page location, link URL, event count, and available source/medium. Treat this as a store-visit proxy, never a download or sale. Do not enable an automatic outbound collector alongside this fallback.

Apple campaign links remain optional. Add only links actually generated in App Store Connect, using the requested campaign name `yutchi_apps_website` where available. Entries under `apple_campaign_links` are keyed by catalog product ID and existing `jp`/`us` region, with `url`, `source:"App Store Connect"`, and `verified_at:"YYYY-MM-DD"`. Preserve real app IDs and `pt`/`ct`/`mt`; no guessed tokens. Empty mappings preserve working untagged links. Campaigns affect CTA links only; structured data retains the original store destination. Apple reports downstream acquisition under its eligibility/privacy conditions; unavailable figures are not zero. [Apple documentation](https://developer.apple.com/help/app-store-connect-analytics/acquisition/campaign-links/).

## Validation, deployment, and rollback

Run:

```sh
python3 scripts/build.py
python3 scripts/check_site.py
node --test tests/analytics-consent.test.cjs
git diff --check
```

The Node tests use offline mocks and do not prove Google Realtime delivery. Before enabling production analytics, review the real settings and consent/privacy obligations, then obtain explicit deployment approval. After approved deployment, validate network requests and cookies in both languages: fresh visit/reject sends no Google requests; accept produces one initial pageview; an approved App Store click produces one click; reject/withdraw/cross-tab revoke stops future collection. Inspect actual payloads for query/email/path leakage and confirm Realtime only after consent. Do not use private sample data. If these checks cannot be completed, keep `enabled:false` and mark HOLD.

For rollback, set `enabled:false`, rebuild, review, and deploy through the approved procedure. Keep the Search Console token and existing URLs. Removing the Google integration entirely also requires removing generated runtime/config/settings entries and revising only the website notice; do not alter app policies or binaries.

## Meta

No Meta Pixel, ad account, retargeting audience, or Conversions API is installed. Existing Open Graph title/description/image metadata is for sharing previews. A future advertising proposal would need separate approval, consent/privacy review, actual payload tests, and a way to disable it; Open Graph metadata does not activate advertising.

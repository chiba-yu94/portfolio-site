# Referral measurement and support navigation

Read-only audit, 2026-10-27. Account analytics and campaign creation were not accessed.

## Current implementation

Generated pages contain 20 App Store anchors pointing to six distinct regional URLs for four products. All have empty query strings: no Apple campaign parameters or UTM parameters. The central catalog retains the expected product IDs and regional destinations. `site.js` only handles catalog filtering; no website analytics script, outbound-click event, or inbound campaign capture was found.

| Question | Available approach | Current limitation |
|---|---|---|
| Are people finding a product through Google? | Search Console Pages/Queries reports | Property access, indexing, and actual metrics were not checked. |
| Does Apple attribute acquisition to this website? | App Store Connect acquisition/referrer reports | Browser/referrer handling and privacy reporting limits apply; actual data was not inspected. |
| Which tagged promotion contributes acquisition? | Apple-generated campaign links | Real links, tokens, campaign availability, and results are unverified. |
| How many visitors click each store button? | No current measurement | Apple campaign results and Google Search clicks are not website button-click counts. |

## Minimal measurement proposal

Use existing App Store Connect Analytics before adding website analytics. Apple's campaign links use `pt` (provider token), `ct` (campaign identifier), and `mt` (media type). Copy actual generated links; do not invent the token or assume one platform's media type applies everywhere. A campaign identifier may have up to 30 characters. Generation requires app analytics data, and reporting is subject to timing and minimum-volume conditions, including five first-time downloads for campaign visibility. Missing data is not a verified zero. Apple counts first-time downloads within 24 hours of a campaign link; when multiple campaign links are used, its documentation gives the most recent link credit for subsequent sales. [Apple campaign documentation](https://developer.apple.com/help/app-store-connect-analytics/acquisition/campaign-links/).

Start with one meaningful campaign per product, for example the proposed identifier `ya_filetransfer_site`. Add language or placement splits only when there is enough data for a useful comparison. Preserve each verified regional App Store URL. Obtain the actual generated links before preparing a catalog/generator change; retain untagged store URLs as the canonical product destinations in structured data. No tracking implementation has been made.

Web Referrer attribution varies by browser and redirect behavior. Do not assume it distinguishes this host's repository paths, languages, or individual buttons. [Apple acquisition documentation](https://developer.apple.com/help/app-store-connect-analytics/acquisition/acquisition/).

Ordinary UTM parameters classify campaigns in a web analytics system. This site has no such collection system, and UTM parameters are not documented substitutes for Apple's campaign parameters. [Google campaign URL guidance](https://support.google.com/analytics/answer/10917952?hl=en). Do not add arbitrary inbound query values to store links or collect visitor identifiers.

Record Search Console search metrics and Apple source/campaign metrics separately over comparable date ranges. They are different populations and cannot establish a visitor-level conversion funnel. Keep unavailable results distinct from zero. No paid service, analytics SDK, new backend, artificial download, or test purchase is proposed.

## Existing support navigation

Five support pages and four representative destinations returned HTTP 200. This was a sample, not a complete external-link/anchor crawl.

- CSV support EN/JA links to privacy, its other language, and the old product top; add contextual links to the existing portfolio catalog and CSV details.
- File Transfer support EN returns to the old Preflight top, which now describes CSV. Add a link to the existing File Transfer details and portfolio catalog, preserving language/privacy links.
- SIGNALS support links to privacy but lacks portfolio navigation. Use the existing product page and `/portfolio-site/en/support/#signals` for an English support entry, rather than implying an English legacy page exists.
- The portfolio support page already links to apps, products, and the other language. MataneNote's existing-guide link points back to the same support URL; replace the redundant affordance with a useful in-page target or remove that duplicate link only in a reviewed future change.

Keep support/privacy URLs and legal text intact. Navigation fixes belong in the appropriate existing repositories; the portfolio's MataneNote change belongs in its generator. No support pages were edited during this audit. Public content and link deployment require approval.

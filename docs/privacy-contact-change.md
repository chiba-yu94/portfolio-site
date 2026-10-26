# Support contact change — October 26, 2026

The public customer-support address is now `yutchi.apps@gmail.com`. This source change updates visible support contact text and `mailto:` destinations. The existing `/support/`, `/privacy/`, and `/matanenote/` routes remain at the same URLs.

The Japanese MataneNote privacy policy retains its original March 22, 2026 establishment date and all four data-handling clauses. Its contact clause points to the new support inbox. The policy notes the contact-only change date. The English page is a labeled translation of that Japanese policy, not a different data-handling policy.

The original document remains in Git history, including the pre-migration `main` revision `bb0bc53`. No historical Git objects have been rewritten. Application-specific policies hosted in the other support repositories remain separate policies.

This is a public support-address migration. It does not change Apple Account credentials, legal seller identity, App Store configuration, application binaries, account login methods, or data-handling behavior.

Project-level `robots.txt` and `sitemap.xml` are provided. Crawlers apply robots rules at the host root; a project file cannot override host-level restrictions. No host-level security or crawler controls are changed by this project.

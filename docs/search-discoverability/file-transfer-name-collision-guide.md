# Investigate case and Unicode filename collisions before sharing files

Editorial draft — not published. Intended for the existing English product/support pages.

A filename collision finding needs a review of the affected entries, not an automatic deletion or rename. File Transfer Preflight can flag case-insensitive and Unicode normalization name collisions in a selected folder or ZIP. It does not compare file contents or decide which version you should keep.

Two names such as `Report.csv` and `report.csv` illustrate a case difference. Unicode-related findings can involve names that look alike while using different character sequences. A warning does not mean two files contain identical data, and the app does not detect every possible visual lookalike.

## 1. Keep the original and inspect a delivery copy

Preserve a known original before making changes. Work on a separate delivery copy so you can review an uncertain change without losing the source material.

Choose the folder or ZIP in File Transfer Preflight and select the intended destination profile. The app checks the selected input locally; it does not connect to the receiving service. ZIP inspection does not extract or rewrite the archive, and symbolic links or aliases are not followed.

If the scan reports an error or incomplete coverage, investigate it first. Scans are bounded to a maximum of 100,000 entries; a partial result must not be treated as a complete check.

## 2. Identify every entry involved

Use the finding's explanation and affected paths to locate the entries in your delivery copy. Review their parent folders as well as their filenames. If useful, export a CSV or HTML report as a review record.

Before changing a name, establish:

- Which files or folders are involved, and whether you need to retain all of them.
- What each entry is for, using your normal document or project tools when necessary.
- Whether documents, project files, or the recipient refer to the existing names.
- Whether the naming decision needs agreement from a colleague or recipient.

Do not infer that one entry is expendable because its name resembles another. File Transfer Preflight checks names, paths, and metadata; it does not establish duplicate content or choose a preferred version.

## 3. Give necessary entries clearly distinct names

If both entries are needed, choose names that communicate their different roles. For example, `report-source.csv` and `report-for-review.csv` may be appropriate if those descriptions match the files. Do not rely only on capitalization or a visually subtle character difference to distinguish two required entries.

Apply changes manually in the delivery copy. If a parent folder is renamed, review references that may depend on its path. For a Unicode-related finding, use the app's explanation as a starting point; do not assume that retyping one character solves the whole issue.

If the input is a ZIP, make the agreed changes in its source delivery folder and create a new archive with your usual tools. File Transfer Preflight has no archive-editing or automatic repair feature. If you cannot confidently identify the entries or their references, pause the rename and ask the owner for clarification.

## 4. Run the same check again

Rescan the edited delivery using the intended destination profile. Include the confirmed destination root if you are also reviewing path length. For Windows, OneDrive, or SharePoint handoffs, the [filename and path workflow](file-transfer-filename-path-guide.md) explains how to use that optional estimate.

Inspect the final rebuilt ZIP if that is what you will send. Check that the relevant finding is resolved and review any new findings introduced by the changed names or folder structure. Keep a simple record of the agreed old-to-new names when the recipient will need it.

If a finding remains, revisit the affected paths and explanation rather than repeatedly guessing at replacements. For support, describe the selected profile, app and macOS versions, the rule ID, and a fictional example that reproduces the issue. Do not send confidential filenames, customer information, or an unreviewed report.

## What a successful recheck means

It means the app did not report that issue under the selected scan conditions. It does not guarantee that the destination will accept every file, preserve every name, or open the contents correctly. Destination policies, permissions, unsupported inputs, and compatibility outside the app's implemented rules need separate review.

Read the [product's scope and limitations](https://chiba-yu94.github.io/portfolio-site/en/apps/file-transfer-preflight/), [existing usage guide](https://chiba-yu94.github.io/preflight-tools-site/file-transfer-preflight/support/), and [app privacy policy](https://chiba-yu94.github.io/preflight-tools-site/file-transfer-preflight/privacy/). For help, use [Yutchi Apps support](https://chiba-yu94.github.io/portfolio-site/en/support/#file-transfer-preflight).

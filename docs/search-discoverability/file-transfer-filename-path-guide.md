# Check filename and path problems before a Windows, OneDrive, or SharePoint handoff

Editorial draft — not published. Intended for the existing English product/support pages.

Before sending a folder or ZIP, check the names and paths in the delivery you actually plan to share. File Transfer Preflight applies destination profiles locally on your Mac and explains potential problems. It does not transfer, rename, delete, move, or rewrite your files.

This workflow is for a handoff that needs review before delivery. If an upload has already failed, use the recipient service's error message alongside the findings; the app does not diagnose live service failures.

## 1. Prepare a delivery copy

Keep the original files intact and work on a separate delivery copy. Confirm which folders and files the recipient expects. A change that makes a name easier to deliver may still affect a document link, project reference, or the recipient's workflow.

A folder scan checks its contents, not the selected folder's own name. Review the delivery folder's name separately.

For a ZIP, select the ZIP you intend to send. File Transfer Preflight inspects ZIP names and metadata without extracting the archive. It does not repair an archive or verify the integrity of its file contents.

## 2. Choose the intended destination

Open File Transfer Preflight, choose the folder or ZIP, and select the profile that matches the handoff:

- **Windows / Office** for a handoff intended for that environment.
- **OneDrive / SharePoint** for a delivery intended for those services.
- **Cross-platform ZIP** when reviewing a ZIP for a broader handoff.

The app applies the selected profile's rules on your Mac. It does not connect to Windows, OneDrive, or SharePoint, inspect an organization's settings, or upload anything.

## 3. Add a destination root only when you know it

The optional destination root lets the app estimate the resulting path length. Include the intended receiving location when you can confirm it with the recipient.

For a cloud profile, the app expects a decoded library path, rather than a sharing URL or the path to your local sync folder. If you cannot establish the correct root, leave it empty. Treat that result as an estimate without the unknown receiving location included.

Do not treat a single character-count rule as a promise that every destination application will accept the delivery. The receiving application, permissions, and organizational policies may require separate checks.

## 4. Review each finding before making changes

Run the scan and read the explanation and suggested action for each relevant finding.

| Finding | A safe next step |
|---|---|
| A name contains a flagged character or reserved name | Confirm the recipient's naming requirements, then choose a meaningful replacement in the delivery copy. |
| Trailing spaces or periods are flagged | Review the full name before changing it; check for a second file that the replacement name could conflict with. |
| A path or filename component is flagged as long | Review both the filename and its parent folders. Consider a shorter, agreed folder structure rather than shortening names blindly. |
| A case or Unicode name collision is flagged | Identify every affected entry before renaming anything. Follow the [collision review workflow](file-transfer-name-collision-guide.md). |
| The scan reports an error or incomplete coverage | Resolve or investigate that condition before treating the delivery as checked. |

Make any approved changes yourself, using your normal file tools. The app's suggested action is guidance; it does not apply a fix.

## 5. Recheck the final delivery

Scan the edited delivery copy again using the intended profile and root. If you rebuild a ZIP after changing its source files, inspect the rebuilt ZIP too. A scan of an earlier folder or archive does not cover a later version.

You can export a CSV or standalone HTML report to record the profile, root, rule IDs, and findings. Review the report before sharing: names, paths, and the destination root can themselves contain confidential information.

File Transfer Preflight checks names, paths, and metadata, with bounded scans of up to 100,000 entries. It does not validate file contents, successful opening in recipient apps, all destination policies, or every compatibility issue. A scan without findings is not a guarantee of transfer success. Where appropriate, ask the recipient to test an agreed sample through the actual receiving workflow.

See [File Transfer Preflight features and limitations](https://chiba-yu94.github.io/portfolio-site/en/apps/file-transfer-preflight/), the [existing usage guide](https://chiba-yu94.github.io/preflight-tools-site/file-transfer-preflight/support/), or [Yutchi Apps support](https://chiba-yu94.github.io/portfolio-site/en/support/#file-transfer-preflight).

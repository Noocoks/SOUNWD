# Android security architecture — SOUNWD

This document defines the security baseline for the Android app as it grows beyond the current placeholder screen. It is a design gate, not a claim that features already exist.

## Current state

The current Kotlin beta is intentionally a static screen. It targets API 36, compiles against API 36, and retains minSdk 23 so older supported Android devices can still install it. Its manifest has no network or storage permission, no WebView, no dynamic code loading, no services, no receivers, no content providers, and no third-party runtime SDKs. Cleartext traffic is disabled and the network security config trusts only the Android system CA store. Do not add any of these just to prepare for future functionality.

## Non-negotiable defaults

1. **Least privilege:** add a permission only with a feature that needs it, a written justification, a user-facing explanation, and a test. Prefer Android system pickers and the Storage Access Framework over broad storage permissions.
2. **No arbitrary execution:** never pass user text, metadata, URLs, filenames, or downloaded content to a shell. Do not use `Runtime.exec`, `ProcessBuilder`, embedded scripting, downloaded plugins, reflection-based plugin loading, or dynamic DEX/native libraries for downloader features.
3. **Network boundaries:** when networking is introduced, use HTTPS only, keep cleartext disabled, rely on Android's system trust store, do not ship permissive trust managers or hostname verifiers, and validate destination hosts against a narrow allowlist before making app-initiated requests. Do not accept arbitrary redirect destinations for privileged requests.
4. **Web content:** do not add a WebView unless a concrete requirement exists. If ever needed, disable JavaScript and file/content access unless essential, never expose a JavaScript bridge to untrusted pages, and restrict navigation.
5. **Storage:** write only to app-private cache/files by default. For user-selected exports, use SAF/MediaStore and scoped access. Normalize and canonicalize paths, reject traversal and symlink escapes, never overwrite existing files without explicit consent, and clean temporary files safely.
6. **Downloaded media:** treat titles, descriptions, thumbnails, subtitles, metadata, filenames, and container contents as hostile input. Bound file sizes and duration where possible, use maintained parsers, avoid automatic opening/execution, and isolate parsing/conversion work.
7. **Components:** every component must be non-exported by default. Only the launcher activity may be exported unless a documented Android integration requires otherwise. Validate every intent action, URI, MIME type, and caller boundary.
8. **Secrets:** never store API keys, signing keys, passwords, or tokens in source control, APK resources, logs, or preferences. Use CI secrets only where needed and protect release signing outside debug workflows.
9. **Logging/privacy:** do not log URLs containing credentials, tokens, local file paths, media metadata, or personal content. Redact exceptions before showing them to users.
10. **Dependencies:** keep runtime dependencies minimal, update through reviewed PRs, audit resolved versions, and pin GitHub Actions to immutable commit SHAs.

## Required gates before adding downloader functionality

- Update the threat model and document the data flow (URL → metadata → download → temporary file → export).
- Add unit tests for URL validation, redirect policy, path traversal, symlink escape, overwrite handling, malformed metadata, and size limits.
- Add instrumentation tests for permission prompts, SAF/MediaStore exports, activity lifecycle, and denied permission paths.
- Run CodeQL, dependency auditing, Android Lint, unit tests, and release build in CI.
- Verify the merged manifest and merged network security config, not only source manifests.
- Produce a signed release artifact using protected signing credentials; never distribute debug APKs as production builds.

## Compatibility and verification matrix

Before a downloader feature is released, test the minimum supported API (23) plus Android 10 (API 29), Android 11 (API 30), Android 16 (API 36), and Android 17 (API 37). Prioritize permission denial, scoped storage/SAF behavior, activity recreation, background restrictions, and edge-to-edge layouts. API 37 behavior changes must be tested before raising targetSdk beyond 36.

## Explicitly deferred

The current beta does not download media. No permissions or network access should be added until the downloader feature is implemented with the controls above. A future feature request does not itself justify a permission.

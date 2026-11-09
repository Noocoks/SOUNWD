# Security policy — SOUNWD

## Supported code and reporting

The active native Android beta in this branch is a minimal, informational screen. It is not the desktop downloader and does not currently need Internet access.

Please report suspected vulnerabilities privately through **GitHub Security Advisories** for this repository (Security → Advisories → Report a vulnerability), rather than publishing exploit details in an issue. Do not include passwords, tokens, private URLs, or personal data in reports.

## Security properties enforced for the Android beta

- No Android permissions are declared.
- No exported component exists except the launcher activity, which has only the MAIN/LAUNCHER intent filter.
- Android app backup is disabled.
- Cleartext HTTP traffic is disabled.
- CI runs CodeQL for Kotlin/Java and Python, dependency review, Python dependency vulnerability auditing, and manifest regression checks.
- CI uses read-only repository permissions except the CodeQL job's narrowly scoped security-events permission and dependency-review's PR-comment permission.

These checks are guardrails, not a proof that software is invulnerable. Any future feature that adds network access, file access, services, receivers, providers, WebViews, native code, or third-party SDKs must include a threat review and tests before merging.

## Scope limitation

This policy and the automated checks in this branch cover the native Android beta and the icon-generation tooling present in this branch. The full desktop downloader and legacy Kivy Android app live on the main branch and are not changed by this PR. They require a separate security patch against main; this PR must not be treated as certification of those components.

## Release guidance

Do not distribute debug APKs as production releases. A production release needs a separately configured release build, protected signing credentials, reproducible dependency versions, and a signed artifact. Never store signing keys or credentials in the repository.

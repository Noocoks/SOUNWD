# SOUNWD security policy

## Scope and reporting

This policy covers the desktop Python downloader, legacy Kivy Android app, native Kotlin Android beta, icon tooling and CI workflows in this repository. Report vulnerabilities privately through GitHub Security Advisories (Security → Advisories → Report a vulnerability). Do not publish exploit instructions, credentials, tokens or personal data in public issues.

## Current controls

- User-supplied download URLs must be HTTPS and use an exact allow-listed YouTube hostname. Userinfo, non-standard ports, whitespace, control characters, host lookalikes and malformed URLs are rejected.
- User-supplied output templates are restricted to a single filename and a small allow-list of yt-dlp fields. Absolute paths, directory separators, traversal, unknown template fields, reserved Windows names and control characters are rejected.
- Download output is resolved under the selected destination; Android downloads remain in app-private storage until explicitly copied to a public media collection.
- Android file sharing revalidates that the file is a regular file inside SOUNWD's private download directory.
- Android requests only the INTERNET permission in the legacy downloader. Do not add broad storage permissions; use MediaStore/Storage Access Framework.
- Android exports and shares files through a small reviewed Java MediaStore bridge compiled into the Kivy app. It validates app-private path containment, rejects symbolic links, enforces a 2 GiB export limit, publishes pending MediaStore entries atomically, and only shares URIs created by the bridge in the current process.
- Python CI runs unit/regression checks, Bandit, pip-audit and CodeQL. The Android build also inspects the compiled APK manifest and network-security resource, not just source configuration. Dependency Review and Dependabot monitor supported dependency ecosystems.
- Bandit suppresses B404/B603/B607 only for reviewed fixed-executable process launches that use argument arrays and no shell; a separate AST regression check rejects shell=True, eval/exec and os.system/os.popen.
- GitHub Actions are pinned to immutable commit SHAs and use least-privilege token permissions where possible.

## Android expansion requirements

The Android downloader is still an early implementation. New capabilities must follow docs/ANDROID_SECURITY.md. In particular, keep downloads private until the user chooses to export/share them, add permissions only for a feature that demonstrably requires them, and never add broad storage, accessibility, overlay, device-admin or root privileges.

## Release requirements

Debug APKs are for testing, not production. A production Android/desktop release needs signed artifacts, protected signing credentials outside the repository, dependency review, successful security scans and a documented release provenance. Do not store signing keys, tokens or credentials in Git.

## Limitations

These controls reduce attack surface and detect regressions; they do not prove software invulnerable. yt-dlp parses untrusted remote metadata and downloads from media hosts. Keep yt-dlp current, review its advisories, and treat downloaded media and metadata as untrusted. The OS sandbox and app-private storage are additional security boundaries, not substitutes for input validation. pip-audit checks the installed host Python environment in CI; it does not prove that every native or cross-compiled python-for-android dependency is vulnerability-free. Android build dependencies and the pinned python-for-android commit still need release-by-release review.

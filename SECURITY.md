# Security policy — SOUNWD

## Reporting vulnerabilities

Please use GitHub Security Advisories → Report a vulnerability for private disclosure. Do not publish exploit details, credentials, tokens, personal data, or private download URLs in public issues.

## Security boundaries

- Only HTTPS links from the exact supported YouTube hostnames are accepted by the download interfaces.
- Advanced output templates are filename-only; path separators, traversal, unknown metadata fields, and unsafe characters are rejected.
- Downloads are staged in a fresh private temporary directory. Only regular audio files are copied into the selected destination, using exclusive no-follow file creation so existing files are never overwritten.
- yt-dlp receives no user-controlled shell command. The application does not use shell=True to launch downloader commands.
- Preferences are size-limited on read and written atomically through a temporary file.
- Desktop/Kivy CI runs Python dependency auditing, unit tests for validation and safe file publication, CodeQL, and OSV-Scanner.
- GitHub Actions are pinned to immutable commit SHAs in the hardened build and security workflows.

## Android beta and future functionality

The separate Kotlin Android beta is currently only a static screen. It must remain permission-free and offline until a real feature requires access. New features must follow the Android security architecture document in the Android beta PR: least privilege, HTTPS-only, no dynamic code loading, app-private staging, SAF/MediaStore exports, hostile-input treatment, and tests for permission denial, path traversal, symlink escape, and overwrite behavior.

## Limitations

These controls reduce attack surface; they do not prove the application invulnerable. yt-dlp, FFmpeg, media extractors, and third-party services process untrusted remote content and must be kept updated. Do not distribute unsigned debug artifacts as production releases. Production releases require protected signing credentials and a dedicated release workflow.

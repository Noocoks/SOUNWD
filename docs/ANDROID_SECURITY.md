# Android security architecture (future SOUNWD features)

The Android Kivy downloader is an early prototype; the separate Kotlin beta is currently only a static placeholder, not the feature-complete mobile application. Security must be designed before feature growth, not bolted on afterwards.

## Baseline

- **Least privilege:** the legacy Kivy app currently needs only INTERNET. Do not add storage, contacts, microphone, camera, location, accessibility, overlay, device-admin or notification permissions pre-emptively.
- **Private by default:** download and process files inside filesDir / app-private storage. Export only after a clear user action through MediaStore or the Storage Access Framework. Never request MANAGE_EXTERNAL_STORAGE.
- **Network:** accept only HTTPS YouTube URLs with exact host allow-list validation at the UI boundary and again immediately before handing the URL to yt-dlp. Reject userinfo, non-standard ports, control characters and host suffix lookalikes. Keep TLS verification enabled; do not install permissive trust managers or accept all certificates.
- **No code execution:** never pass user input to a shell, eval, exec, a scripting engine or a dynamic class name. Process invocations must use argument arrays and fixed executable paths. Do not load plugins/scripts from downloaded media or remote metadata. The Kivy MediaStore bridge resolves one fixed `org.kivy.android.PythonActivity` class name only to obtain its current Activity; that name must never come from user or remote data.
- **Untrusted content:** titles, uploader names, thumbnails, subtitles, metadata and filenames from remote sources are hostile input. Escape them in UI, sanitize filenames, limit lengths and never use them as filesystem paths.
- **No WebView by default:** if a future feature truly requires one, disable JavaScript and file/content access unless specifically needed, disallow mixed content, restrict navigation to a strict allow-list, and do not expose a JavaScript bridge to untrusted pages.
- **Background work:** use WorkManager for deferrable work. Add a foreground service only if a user-visible long-running task requires it, with a narrowly scoped service type and notification.
- **Sharing:** use content URIs / MediaStore and temporary read grants. Never expose raw filesystem paths or a world-readable provider.
- **Secrets:** do not store YouTube credentials, cookies or API tokens in plaintext preferences, logs, source code or build artifacts. If account integration is ever introduced, use Android Keystore-backed storage and an explicit consent flow.
- **Logging:** never log URLs containing credentials, cookies, headers, tokens, full environment variables, private paths or media metadata. Logs must remain app-private and bounded.
- **Updates:** pin and review Android Gradle Plugin, Kotlin, Gradle, Buildozer, python-for-android and Python dependencies. Run CodeQL, dependency auditing and APK manifest inspection on every release.

## Permission change gate

Every new permission requires a PR explanation of:
1. The user-visible feature that requires it.
2. Why a less-privileged Android API cannot achieve the same result.
3. The exact runtime request moment and denial behaviour.
4. Tests proving unrelated flows still work without the permission.
5. A review of privacy implications and data retention.

## Target architecture

Prefer a small native Kotlin shell with isolated components:
- DownloadCoordinator: validates requests and schedules work; no UI or storage privileges.
- DownloadEngine: wraps yt-dlp/native tooling; accepts a validated immutable request, not raw UI strings.
- PrivateDownloadStore: owns app-private temporary files and enforces canonical-path containment.
- MediaExporter: exports one completed file through MediaStore/SAF after user confirmation.
- ShareCoordinator: shares only validated content URIs with temporary grants.
- SettingsStore: stores non-secret preferences only.
- UI/ViewModels: display state and never construct shell commands or filesystem paths.

Each component should have unit tests for malformed input, cancellation, permission denial, path traversal, symlink attempts, corrupted metadata, partial downloads and cleanup. The current androidstorage4kivy bridge is pinned to 0.1.1 because its upstream repository was archived in 2023. It is an acknowledged maintenance/supply-chain risk, not a long-term foundation. Replace it with a small reviewed Kotlin MediaStore/Share implementation before expanding Android storage features. Treat the Kivy implementation as a compatibility prototype until the native Kotlin downloader replaces it; do not mix the two runtimes or migrate functionality without device tests.

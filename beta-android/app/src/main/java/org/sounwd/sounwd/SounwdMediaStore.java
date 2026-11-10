package org.sounwd.sounwd;

import android.content.ClipData;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Intent;
import android.net.Uri;
import android.os.Environment;
import android.provider.MediaStore;

import android.app.Activity;

import java.lang.reflect.Field;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class SounwdMediaStore {
    private static final long MAX_AUDIO_BYTES = 2L * 1024L * 1024L * 1024L;
    private static final int MAX_EXPORTED_FILES = 500;
    private static final Set<String> EXPORTED_URIS = Collections.synchronizedSet(new HashSet<String>());

    private SounwdMediaStore() {}

    public static String exportAudio(String privateRoot, String sourcePath, String collection) throws Exception {
        if (privateRoot == null || sourcePath == null) {
            throw new IllegalArgumentException("Invalid private audio path.");
        }

        File rawSource = new File(sourcePath);
        if (java.nio.file.Files.isSymbolicLink(rawSource.toPath())) {
            throw new SecurityException("Symbolic links are not accepted.");
        }

        File root = new File(privateRoot).getCanonicalFile();
        File source = rawSource.getCanonicalFile();
        String rootPrefix = root.getPath() + File.separator;
        if (!source.getPath().startsWith(rootPrefix) || !source.isFile()) {
            throw new SecurityException("Audio file is outside the app-private directory.");
        }
        if (source.length() <= 0 || source.length() > MAX_AUDIO_BYTES) {
            throw new SecurityException("Audio file size is outside the permitted range.");
        }

        String fileName = source.getName();
        String extension = fileName.contains(".")
                ? fileName.substring(fileName.lastIndexOf('.') + 1).toLowerCase()
                : "";
        String mime = mimeForExtension(extension);
        if (mime == null || fileName.length() > 240 || fileName.contains("..")
                || fileName.startsWith(".") || fileName.endsWith(".") || fileName.endsWith(" ")) {
            throw new SecurityException("Unsupported or unsafe audio filename.");
        }
        for (int index = 0; index < fileName.length(); index++) {
            char character = fileName.charAt(index);
            if (Character.isISOControl(character) || Character.getType(character) == Character.FORMAT
                    || "/\\\\:*?\\"<>|".indexOf(character) >= 0) {
                throw new SecurityException("Audio filename contains unsafe characters.");
            }
        }

        final String relativePath;
        if (Environment.DIRECTORY_MUSIC.equals(collection)) {
            relativePath = Environment.DIRECTORY_MUSIC + "/SOUNWD";
        } else if (Environment.DIRECTORY_DOWNLOADS.equals(collection)) {
            relativePath = Environment.DIRECTORY_DOWNLOADS + "/SOUNWD";
        } else {
            throw new SecurityException("Unsupported MediaStore collection.");
        }

        Activity activity = getActivity();
        ContentResolver resolver = activity.getContentResolver();
        ContentValues values = new ContentValues();
        values.put(MediaStore.MediaColumns.DISPLAY_NAME, fileName);
        values.put(MediaStore.MediaColumns.MIME_TYPE, mime);
        values.put(MediaStore.MediaColumns.RELATIVE_PATH, relativePath);
        values.put(MediaStore.MediaColumns.IS_PENDING, 1);

        Uri inserted = resolver.insert(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, values);
        if (inserted == null) {
            throw new IllegalStateException("MediaStore could not create the audio entry.");
        }

        try {
            long copied = 0;
            try (InputStream input = new BufferedInputStream(new FileInputStream(source));
                 OutputStream output = new BufferedOutputStream(resolver.openOutputStream(inserted, "w"))) {
                if (output == null) {
                    throw new IllegalStateException("MediaStore output stream is unavailable.");
                }
                byte[] buffer = new byte[64 * 1024];
                int count;
                while ((count = input.read(buffer)) != -1) {
                    copied += count;
                    if (copied > MAX_AUDIO_BYTES) {
                        throw new SecurityException("Audio export exceeded the size limit.");
                    }
                    output.write(buffer, 0, count);
                }
            }

            if (copied != source.length()) {
                throw new IllegalStateException("Audio export was incomplete.");
            }
            ContentValues publish = new ContentValues();
            publish.put(MediaStore.MediaColumns.IS_PENDING, 0);
            if (resolver.update(inserted, publish, null, null) != 1) {
                throw new IllegalStateException("MediaStore could not publish the audio.");
            }
            String uriValue = inserted.toString();
            synchronized (EXPORTED_URIS) {
                if (EXPORTED_URIS.size() >= MAX_EXPORTED_FILES) {
                    resolver.delete(inserted, null, null);
                    throw new SecurityException("Too many audio files in one export batch.");
                }
                EXPORTED_URIS.add(uriValue);
            }
            return uriValue;
        } catch (Exception error) {
            resolver.delete(inserted, null, null);
            throw error;
        }
    }

    public static void shareAudioList(List<String> uriStrings) throws Exception {
        if (uriStrings == null || uriStrings.isEmpty() || uriStrings.size() > MAX_EXPORTED_FILES) {
            throw new IllegalArgumentException("Invalid audio share list.");
        }
        Activity activity = getActivity();

        ArrayList<Uri> uris = new ArrayList<>();
        ClipData clip = null;
        for (String value : uriStrings) {
            if (value == null || !EXPORTED_URIS.contains(value)) {
                throw new SecurityException("Only files exported by SOUNWD may be shared.");
            }
            Uri uri = Uri.parse(value);
            if (!"content".equals(uri.getScheme()) || !"media".equals(uri.getAuthority())) {
                throw new SecurityException("Only SOUNWD MediaStore content URIs may be shared.");
            }
            uris.add(uri);
            if (clip == null) {
                clip = ClipData.newUri(activity.getContentResolver(), "SOUNWD audio", uri);
            } else {
                clip.addItem(new ClipData.Item(uri));
            }
        }

        Intent send = new Intent(uris.size() == 1 ? Intent.ACTION_SEND : Intent.ACTION_SEND_MULTIPLE);
        send.setType("audio/*");
        if (uris.size() == 1) {
            send.putExtra(Intent.EXTRA_STREAM, uris.get(0));
        } else {
            send.putParcelableArrayListExtra(Intent.EXTRA_STREAM, uris);
        }
        send.setClipData(clip);
        send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        activity.startActivity(Intent.createChooser(send, "Compartir audio"));
    }


    public static void beginExportBatch() {
        EXPORTED_URIS.clear();
    }

    public static void abortExportBatch() throws Exception {
        Activity activity = getActivity();
        ArrayList<String> pending;
        synchronized (EXPORTED_URIS) {
            pending = new ArrayList<>(EXPORTED_URIS);
            EXPORTED_URIS.clear();
        }
        ContentResolver resolver = activity.getContentResolver();
        for (String value : pending) {
            try {
                resolver.delete(Uri.parse(value), null, null);
            } catch (RuntimeException ignored) {
                // Continue cleanup of the remaining rows.
            }
        }
    }

    private static Activity getActivity() throws Exception {
        Class<?> activityClass = Class.forName("org.kivy.android.PythonActivity");
        Field activityField = activityClass.getField("mActivity");
        Object value = activityField.get(null);
        if (!(value instanceof Activity)) {
            throw new IllegalStateException("Android activity is unavailable.");
        }
        return (Activity) value;
    }

    private static String mimeForExtension(String extension) {
        switch (extension) {
            case "mp3": return "audio/mpeg";
            case "m4a": return "audio/mp4";
            case "aac": return "audio/aac";
            case "flac": return "audio/flac";
            case "ogg":
            case "opus": return "audio/ogg";
            case "wav": return "audio/wav";
            case "weba":
            case "webm": return "audio/webm";
            case "mka": return "audio/x-matroska";
            default: return null;
        }
    }
}

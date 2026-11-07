package org.sounwd

import android.app.Activity
import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import java.net.URLDecoder
import java.nio.charset.StandardCharsets

class MainActivity : Activity() {
    private lateinit var address: EditText
    private lateinit var status: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(28, 36, 28, 24)
        }

        val title = TextView(this).apply {
            text = "SOUNWD"
            textSize = 32f
            gravity = Gravity.CENTER
        }
        root.addView(title, matchWrap())

        val subtitle = TextView(this).apply {
            text = "Beta · Descargas de audio"
            textSize = 16f
            gravity = Gravity.CENTER
            setPadding(0, 8, 0, 28)
        }
        root.addView(subtitle, matchWrap())

        address = EditText(this).apply {
            hint = "https://ejemplo.com/audio.mp3"
            textSize = 16f
            singleLine = true
            inputType = android.text.InputType.TYPE_CLASS_TEXT or
                android.text.InputType.TYPE_TEXT_VARIATION_URI
        }
        root.addView(address, matchWrap())

        val download = Button(this).apply {
            text = "Descargar audio"
            setOnClickListener { startDownload() }
        }
        root.addView(download, matchWrap())

        status = TextView(this).apply {
            text = "Pega un enlace directo a un archivo de audio."
            textSize = 14f
            setPadding(0, 18, 0, 0)
        }
        root.addView(status, matchWrap())

        val note = TextView(this).apply {
            text = "Esta primera beta admite enlaces directos HTTP/HTTPS a archivos. Todavía no descarga vídeos ni enlaces de YouTube."
            textSize = 13f
            setPadding(0, 24, 0, 0)
        }
        root.addView(note, matchWrap())

        setContentView(root)
    }

    private fun startDownload() {
        val raw = address.text.toString().trim()
        val uri = runCatching { Uri.parse(raw) }.getOrNull()
        if (uri == null || uri.scheme !in listOf("http", "https") || uri.host.isNullOrBlank()) {
            status.text = "Introduce un enlace HTTP o HTTPS válido."
            return
        }

        val pathName = uri.lastPathSegment?.let {
            URLDecoder.decode(it, StandardCharsets.UTF_8.name())
        }?.takeIf { it.isNotBlank() && it.contains('.') } ?: "audio"

        try {
            val request = DownloadManager.Request(uri)
                .setTitle(pathName)
                .setDescription("Descargando con SOUNWD")
                .setNotificationVisibility(
                    DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED
                )
                .setAllowedOverMetered(true)
                .setAllowedOverRoaming(false)

            val manager = getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
            manager.enqueue(request)
            status.text = "Descarga iniciada. Consulta la notificación y la carpeta Descargas."
        } catch (_: Exception) {
            status.text = "No se pudo iniciar la descarga. Comprueba el enlace e inténtalo de nuevo."
        }
    }

    private fun matchWrap() = LinearLayout.LayoutParams(
        ViewGroup.LayoutParams.MATCH_PARENT,
        ViewGroup.LayoutParams.WRAP_CONTENT
    )
}

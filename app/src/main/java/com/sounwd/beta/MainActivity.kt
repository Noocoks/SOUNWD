package com.sounwd.beta

import android.app.Activity
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.util.Log
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import kotlin.math.max

private const val TAG = "SOUNWD"

private object Brand {
    const val BG = 0xFF09090B.toInt()
    const val PANEL = 0xFF151519.toInt()
    const val RED = 0xFFB20F32.toInt()
    const val WHITE = 0xFFF0F0F2.toInt()
    const val MUTED = 0xFF858B93.toInt()
}

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.i(TAG, "MainActivity.onCreate started")

        try {
            renderBrandScreen()
            Log.i(TAG, "Brand screen rendered successfully")
        } catch (error: Exception) {
            Log.e(TAG, "Brand screen failed; showing safe fallback", error)
            renderSafeFallback()
        }
    }

    private fun renderBrandScreen() {
        window.statusBarColor = Brand.BG
        window.navigationBarColor = Brand.BG

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Brand.BG)
        }
        val scroll = ScrollView(this).apply {
            isFillViewport = true
            clipToPadding = false
            setPadding(dp(22), dp(30), dp(22), dp(28))
        }
        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
        }

        // The artwork is optional at runtime: a missing or malformed icon must
        // never prevent the actual application screen from opening.
        val bitmap = loadBrandBitmap()
        if (bitmap != null) {
            val emblem = ImageView(this).apply {
                setImageBitmap(bitmap)
                scaleType = ImageView.ScaleType.FIT_CENTER
                contentDescription = "SOUNWD"
            }
            content.addView(
                emblem,
                LinearLayout.LayoutParams(dp(104), dp(104)).apply {
                    bottomMargin = dp(14)
                }
            )
        } else {
            Log.w(TAG, "Brand image unavailable; continuing without the in-app emblem")
        }

        content.addView(text("SOUNWD", 30f, Brand.WHITE, true, Gravity.CENTER))
        content.addView(
            text("YOUR SOUND. YOUR MOMENTS.", 10f, Brand.MUTED, true, Gravity.CENTER).apply {
                letterSpacing = 0.18f
                setPadding(0, dp(7), 0, dp(30))
            }
        )

        val panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            background = rounded(Brand.PANEL, 20)
            setPadding(dp(22), dp(28), dp(22), dp(28))
        }
        val mark = View(this).apply { background = rounded(Brand.RED, 50) }
        panel.addView(
            mark,
            LinearLayout.LayoutParams(dp(34), dp(4)).apply { bottomMargin = dp(20) }
        )
        panel.addView(text("SOUNWD se ha abierto", 20f, Brand.WHITE, true, Gravity.CENTER))
        panel.addView(
            text("Tu espacio de sonido está listo.", 14f, Brand.MUTED, false, Gravity.CENTER).apply {
                setPadding(0, dp(12), 0, 0)
            }
        )
        content.addView(
            panel,
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            ).apply { topMargin = dp(12) }
        )
        content.addView(
            text("UNA EXPERIENCIA SOUNWD", 10f, Brand.RED, true, Gravity.CENTER).apply {
                letterSpacing = 0.16f
                setPadding(0, dp(34), 0, dp(10))
            }
        )
        content.addView(
            text(
                "Esta primera beta es una base visual. Iremos incorporando las funciones paso a paso.",
                13f,
                Brand.MUTED,
                false,
                Gravity.CENTER
            ).apply { setPadding(dp(8), 0, dp(8), 0) }
        )

        scroll.addView(content)
        root.addView(
            scroll,
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        )
        setContentView(root)
    }

    private fun loadBrandBitmap(): Bitmap? {
        val resourceId = resources.getIdentifier("sounwd_mark", "drawable", packageName)
        if (resourceId == 0) return null

        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        resources.openRawResource(resourceId).use { stream ->
            BitmapFactory.decodeStream(stream, null, bounds)
        }
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null

        val largestSide = max(bounds.outWidth, bounds.outHeight)
        var sampleSize = 1
        while (largestSide / sampleSize > 512) sampleSize *= 2

        val options = BitmapFactory.Options().apply { inSampleSize = sampleSize }
        return resources.openRawResource(resourceId).use { stream ->
            BitmapFactory.decodeStream(stream, null, options)
        }
    }

    private fun renderSafeFallback() {
        try {
            window.statusBarColor = Brand.BG
            window.navigationBarColor = Brand.BG
            val fallback = TextView(this).apply {
                text = "SOUNWD se ha abierto"
                textSize = 20f
                setTextColor(Color.WHITE)
                gravity = Gravity.CENTER
                setBackgroundColor(Brand.BG)
                typeface = Typeface.create("sans-serif", Typeface.BOLD)
            }
            setContentView(fallback)
            Log.i(TAG, "Safe fallback screen rendered")
        } catch (fallbackError: Exception) {
            Log.e(TAG, "Even the safe fallback screen failed", fallbackError)
            throw fallbackError
        }
    }

    private fun text(value: String, size: Float, color: Int, bold: Boolean, gravity: Int) =
        TextView(this).apply {
            text = value
            textSize = size
            setTextColor(color)
            this.gravity = gravity
            typeface = if (bold) {
                Typeface.create("sans-serif", Typeface.BOLD)
            } else {
                Typeface.create("sans-serif", Typeface.NORMAL)
            }
        }

    private fun rounded(color: Int, radius: Int) = GradientDrawable().apply {
        setColor(color)
        cornerRadius = dp(radius).toFloat()
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()
}

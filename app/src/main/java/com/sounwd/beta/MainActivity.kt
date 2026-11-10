package com.sounwd.beta

import android.app.Activity
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.os.Build
import android.view.WindowInsetsController
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

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
        if (Build.VERSION.SDK_INT < 35) {
            @Suppress("DEPRECATION")
            run {
                window.statusBarColor = Brand.BG
                window.navigationBarColor = Brand.BG
            }
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.insetsController?.setSystemBarsAppearance(
                0,
                WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS or
                    WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS
            )
        } else {
            @Suppress("DEPRECATION")
            run { window.decorView.systemUiVisibility = 0 }
        }

        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setBackgroundColor(Brand.BG) }
        val scroll = ScrollView(this).apply {
            isFillViewport = true
            clipToPadding = false
            setPadding(dp(22), dp(30), dp(22), dp(28))
        }
        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
        }
        val emblem = ImageView(this).apply {
            setImageResource(R.drawable.sounwd_mark)
            scaleType = ImageView.ScaleType.FIT_CENTER
            contentDescription = "SOUNWD"
        }
        content.addView(emblem, LinearLayout.LayoutParams(dp(104), dp(104)).apply { bottomMargin = dp(14) })
        content.addView(text("SOUNWD", 30f, Brand.WHITE, true, Gravity.CENTER))
        content.addView(text("YOUR SOUND. YOUR MOMENTS.", 10f, Brand.MUTED, true, Gravity.CENTER).apply {
            letterSpacing = 0.18f
            setPadding(0, dp(7), 0, dp(30))
        })
        val panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            background = rounded(Brand.PANEL, 20)
            setPadding(dp(22), dp(28), dp(22), dp(28))
        }
        val mark = View(this).apply { background = rounded(Brand.RED, 50) }
        panel.addView(mark, LinearLayout.LayoutParams(dp(34), dp(4)).apply { bottomMargin = dp(20) })
        panel.addView(text("SOUNWD se ha abierto", 20f, Brand.WHITE, true, Gravity.CENTER))
        panel.addView(text("Tu espacio de sonido está listo.", 14f, Brand.MUTED, false, Gravity.CENTER).apply {
            setPadding(0, dp(12), 0, 0)
        })
        content.addView(panel, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
            topMargin = dp(12)
        })
        content.addView(text("UNA EXPERIENCIA SOUNWD", 10f, Brand.RED, true, Gravity.CENTER).apply {
            letterSpacing = 0.16f
            setPadding(0, dp(34), 0, dp(10))
        })
        content.addView(text(
            "Esta primera beta es una base visual. Iremos incorporando las funciones paso a paso.",
            13f, Brand.MUTED, false, Gravity.CENTER
        ).apply { setPadding(dp(8), 0, dp(8), 0) })
        scroll.addView(content)
        root.addView(scroll, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        setContentView(root)
    }

    private fun text(value: String, size: Float, color: Int, bold: Boolean, gravity: Int) =
        TextView(this).apply {
            text = value
            textSize = size
            setTextColor(color)
            this.gravity = gravity
            typeface = if (bold) Typeface.create("sans-serif", Typeface.BOLD) else Typeface.create("sans-serif", Typeface.NORMAL)
        }

    private fun rounded(color: Int, radius: Int) = GradientDrawable().apply {
        setColor(color)
        cornerRadius = dp(radius).toFloat()
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()
}

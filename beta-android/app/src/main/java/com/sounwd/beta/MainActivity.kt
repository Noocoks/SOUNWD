package com.sounwd.beta

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val message = TextView(this).apply {
            text = "SOUNWD se ha abierto"
            setTextColor(Color.WHITE)
            textSize = 22f
            gravity = Gravity.CENTER
            setBackgroundColor(Color.rgb(48, 48, 48))
        }

        window.statusBarColor = Color.rgb(48, 48, 48)
        window.navigationBarColor = Color.rgb(48, 48, 48)
        window.decorView.setBackgroundColor(Color.rgb(48, 48, 48))
        setContentView(message)
    }
}

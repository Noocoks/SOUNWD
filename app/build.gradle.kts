plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.sounwd.beta"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.sounwd.beta"
        minSdk = 23
        targetSdk = 35
        versionCode = 1
        versionName = "0.0.1"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
}

configurations.configureEach {
    resolutionStrategy.activateDependencyLocking()
}

dependencyLocking {
    lockAllConfigurations()
}

android {
    lint {
        abortOnError = true
        checkReleaseBuilds = true
        warningsAsErrors = true
    }
}

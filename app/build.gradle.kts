plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.sounwd.beta"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.sounwd.beta"
        minSdk = 29
        targetSdk = 36
        versionCode = 1
        versionName = "0.0.1"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
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

kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}

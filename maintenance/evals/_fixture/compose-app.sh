#!/bin/bash
# Fixture for the trigger suite: a small Jetpack Compose app with one spec and its index.
set -euo pipefail

P=app/src/main/kotlin/com/example/greeter
T=app/src/test/kotlin/com/example/greeter
mkdir -p gradle "$P/greeting" "$T/greeting" app/src/main/res/values docs/specs

cat > settings.gradle.kts <<'EOF'
pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement { repositories { google(); mavenCentral() } }
rootProject.name = "Greeter"
include(":app")
EOF

cat > gradle/libs.versions.toml <<'EOF'
[versions]
agp = "9.5.0"
kotlin = "2.4.21"
composeBom = "2026.09.00"
lifecycle = "2.11.0"
navigation = "2.9.6"
robolectric = "4.18"

[libraries]
androidx-compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "composeBom" }
androidx-material3 = { group = "androidx.compose.material3", name = "material3" }
androidx-lifecycle-viewmodel-compose = { group = "androidx.lifecycle", name = "lifecycle-viewmodel-compose", version.ref = "lifecycle" }
androidx-lifecycle-runtime-compose = { group = "androidx.lifecycle", name = "lifecycle-runtime-compose", version.ref = "lifecycle" }
androidx-navigation-compose = { group = "androidx.navigation", name = "navigation-compose", version.ref = "navigation" }
junit = { group = "junit", name = "junit", version = "4.13.2" }
robolectric = { group = "org.robolectric", name = "robolectric", version.ref = "robolectric" }
androidx-ui-test-junit4 = { group = "androidx.compose.ui", name = "ui-test-junit4" }

[plugins]
android-application = { id = "com.android.application", version.ref = "agp" }
kotlin-compose = { id = "org.jetbrains.kotlin.plugin.compose", version.ref = "kotlin" }
EOF

cat > app/build.gradle.kts <<'EOF'
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "com.example.greeter"
    compileSdk = 36
    defaultConfig {
        applicationId = "com.example.greeter"
        minSdk = 24
        versionCode = 3
        versionName = "1.2.0"
    }
    buildFeatures { compose = true }
    testOptions { unitTests { isIncludeAndroidResources = true } }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.material3)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.navigation.compose)
    testImplementation(libs.junit)
    testImplementation(libs.robolectric)
    testImplementation(libs.androidx.ui.test.junit4)
}
EOF

cat > "$P/greeting/GreetingViewModel.kt" <<'EOF'
package com.example.greeter.greeting

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

data class GreetingUiState(val waved: Boolean = false)

class GreetingViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(GreetingUiState())
    val uiState = _uiState.asStateFlow()

    fun wave() = _uiState.update { it.copy(waved = true) }
}
EOF

cat > "$P/greeting/GreetingScreen.kt" <<'EOF'
package com.example.greeter.greeting

import androidx.compose.foundation.layout.Column
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.greeter.R

@Composable
fun GreetingRoute(viewModel: GreetingViewModel = viewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    GreetingScreen(uiState = uiState, onWave = viewModel::wave)
}

@Composable
fun GreetingScreen(uiState: GreetingUiState, onWave: () -> Unit, modifier: Modifier = Modifier) {
    Column(modifier) {
        Text(stringResource(if (uiState.waved) R.string.greeting_waved else R.string.greeting_hello))
        Button(onClick = onWave) { Text(stringResource(R.string.greeting_wave)) }
    }
}
EOF

cat > "$T/greeting/GreetingScreenTest.kt" <<'EOF'
package com.example.greeter.greeting

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.assertIsDisplayed
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class GreetingScreenTest {
    @get:Rule val compose = createComposeRule()

    @Test
    fun `greeting_1 Waved`() {
        compose.setContent { GreetingRoute() }
        compose.onNodeWithText("Wave").performClick()
        compose.onNodeWithText("You waved!").assertIsDisplayed()
    }
}
EOF

cat > app/src/main/res/values/strings.xml <<'EOF'
<resources>
    <string name="app_name">Greeter</string>
    <string name="greeting_hello">Hello!</string>
    <string name="greeting_wave">Wave</string>
    <string name="greeting_waved">You waved!</string>
</resources>
EOF

cat > docs/specs/greeting-feature-spec.md <<'EOF'
# Greeting

> Last verified: 2026-11-10 (commit 4d5e6f7)

## 1. Summary
The start screen greets the user, who can wave back.

## 6. Behavior

### Requirement: Waving
<!-- id: greeting.1 -->
<!-- screen: GreetingScreen -->
<!-- entities: none -->
<!-- enforced: app/src/main/kotlin/com/example/greeter/greeting/GreetingViewModel.kt#GreetingViewModel.wave -->

#### Scenario: Waved
<!-- test: app/src/test/kotlin/com/example/greeter/greeting/GreetingScreenTest.kt#greeting_1 Waved -->
- WHEN the user taps Wave
- THEN the greeting reads "You waved!"
EOF

cat > docs/specs/index.md <<'EOF'
| Feature | Spec | Screens and routes | Status | Last verified |
|---|---|---|---|---|
| Greeting | [greeting-feature-spec.md](greeting-feature-spec.md) | GreetingScreen (start) | implemented | 2026-11-10 (commit 4d5e6f7) |
EOF

git init -q
git add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -qm "fixture"

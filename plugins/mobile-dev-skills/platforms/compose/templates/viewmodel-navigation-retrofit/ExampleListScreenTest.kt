// Template: Compose tests for a screen's section 6 scenarios, on the JVM under Robolectric.
//
// Each test's name is the requirement id and the scenario title, exactly as the spec
// writes them, with the characters standards.md's "Form" lists (the id's `.`) written as `_`.
// The spec's `test` anchors point at that name.
//
// Adjust to match project conventions:
//   - Wrap the screen in the app's theme.
//   - Does the project have a shared helper that sets content with its theme? Use it.

package com.example.app.example

import android.content.Context
import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.example.app.R
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ExampleListScreenTest {
    // The v2 rule needs Compose UI 1.11; before it, import androidx.compose.ui.test.junit4.createComposeRule.
    @get:Rule
    val composeRule = createComposeRule()

    private val context: Context = ApplicationProvider.getApplicationContext()

    private fun setScreen(uiState: ExampleListUiState, onRefresh: () -> Unit = {}) {
        composeRule.setContent {
            MaterialTheme {
                ExampleListScreen(uiState = uiState, onRefresh = onRefresh, onExampleClick = {})
            }
        }
    }

    @Test
    fun `example-list_1 Loading`() {
        setScreen(ExampleListUiState.Loading)

        composeRule.onNodeWithTag(EXAMPLE_LIST_LOADING_TAG).assertIsDisplayed()
    }

    @Test
    fun `example-list_1 Error`() {
        setScreen(ExampleListUiState.Error)

        composeRule.onNodeWithText(context.getString(R.string.example_list_error)).assertIsDisplayed()
        composeRule.onNodeWithText(context.getString(R.string.example_list_retry)).assertIsDisplayed()
    }

    @Test
    fun `example-list_1 Empty`() {
        setScreen(ExampleListUiState.Empty)

        composeRule.onNodeWithText(context.getString(R.string.example_list_empty)).assertIsDisplayed()
    }

    @Test
    fun `example-list_1 Success`() {
        setScreen(ExampleListUiState.Success(listOf(Example(id = "1", name = "First"))))

        composeRule.onNodeWithText("First").assertIsDisplayed()
    }

    @Test
    fun `example-list_2 Retry`() {
        var refreshes = 0
        setScreen(ExampleListUiState.Error, onRefresh = { refreshes++ })

        composeRule.onNodeWithText(context.getString(R.string.example_list_retry)).performClick()

        assertEquals(1, refreshes)
    }
}

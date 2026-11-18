// Template: a type-safe route and its destination in the navigation graph.
// Adjust to match project conventions:
//   - One NavHost file, or a NavGraphBuilder extension per feature like this one? Add the destination there.
//   - A destination with arguments is a data class (`data class ExampleDetailDestination(val id: String)`),
//     which its ViewModel reads with `savedStateHandle.toRoute<ExampleDetailDestination>()`.
//   - A deep link adds `deepLinks = listOf(navDeepLink<…>(basePath = "https://example.com/examples"))`
//     to `composable<…>`, and an <intent-filter> to the activity.

package com.example.app.example

import androidx.navigation.NavGraphBuilder
import androidx.navigation.compose.composable
import kotlinx.serialization.Serializable

// Not `ExampleListRoute`: that is the stateful composable's name.
@Serializable
data object ExampleListDestination

fun NavGraphBuilder.exampleListScreen(onExampleClick: (String) -> Unit) {
    composable<ExampleListDestination> {
        ExampleListRoute(onExampleClick = onExampleClick)
    }
}

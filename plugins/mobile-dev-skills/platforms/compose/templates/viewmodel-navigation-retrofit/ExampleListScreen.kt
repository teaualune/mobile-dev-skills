// Template: a stateful route and its stateless screen, with the four states in one `when`.
// Adjust to match project conventions:
//   - Shared loading, error and empty composables? Use them instead of the ones below.
//   - The app's theme in the previews, and its spacing values instead of literal dp.
//   - Does the NavHost already sit in a Scaffold with a top bar? Then drop this Scaffold.
//   - Add each string (example_list_title, _error, _retry, _empty) to every values-<locale>/strings.xml.

package com.example.app.example

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.app.R

const val EXAMPLE_LIST_LOADING_TAG = "example_list_loading"

@Composable
fun ExampleListRoute(
    onExampleClick: (String) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ExampleListViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    ExampleListScreen(
        uiState = uiState,
        onRefresh = viewModel::refresh,
        onExampleClick = onExampleClick,
        modifier = modifier,
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ExampleListScreen(
    uiState: ExampleListUiState,
    onRefresh: () -> Unit,
    onExampleClick: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        modifier = modifier,
        topBar = { TopAppBar(title = { Text(stringResource(R.string.example_list_title)) }) },
    ) { innerPadding ->
        PullToRefreshBox(
            isRefreshing = uiState is ExampleListUiState.Success && uiState.isRefreshing,
            onRefresh = onRefresh,
            modifier = Modifier.padding(innerPadding).fillMaxSize(),
        ) {
            when (uiState) {
                ExampleListUiState.Loading -> StateContent {
                    CircularProgressIndicator(Modifier.testTag(EXAMPLE_LIST_LOADING_TAG))
                }
                ExampleListUiState.Error -> StateContent {
                    Text(stringResource(R.string.example_list_error))
                    Button(onClick = onRefresh) {
                        Text(stringResource(R.string.example_list_retry))
                    }
                }
                ExampleListUiState.Empty -> StateContent {
                    Text(stringResource(R.string.example_list_empty))
                }
                is ExampleListUiState.Success -> LazyColumn(Modifier.fillMaxSize()) {
                    items(uiState.items, key = { it.id }) { item ->
                        ListItem(
                            headlineContent = { Text(item.name) },
                            modifier = Modifier.clickable { onExampleClick(item.id) },
                        )
                    }
                }
            }
        }
    }
}

// Fills the box and scrolls, so pull to refresh works in this state too.
@Composable
private fun StateContent(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(
        modifier = modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp, Alignment.CenterVertically),
        horizontalAlignment = Alignment.CenterHorizontally,
        content = content,
    )
}

@Preview
@Composable
private fun ExampleListLoadingPreview() {
    MaterialTheme {
        ExampleListScreen(ExampleListUiState.Loading, onRefresh = {}, onExampleClick = {})
    }
}

@Preview
@Composable
private fun ExampleListErrorPreview() {
    MaterialTheme {
        ExampleListScreen(ExampleListUiState.Error, onRefresh = {}, onExampleClick = {})
    }
}

@Preview
@Composable
private fun ExampleListEmptyPreview() {
    MaterialTheme {
        ExampleListScreen(ExampleListUiState.Empty, onRefresh = {}, onExampleClick = {})
    }
}

@Preview
@Composable
private fun ExampleListSuccessPreview() {
    MaterialTheme {
        ExampleListScreen(
            ExampleListUiState.Success(listOf(Example(id = "1", name = "First"))),
            onRefresh = {},
            onExampleClick = {},
        )
    }
}

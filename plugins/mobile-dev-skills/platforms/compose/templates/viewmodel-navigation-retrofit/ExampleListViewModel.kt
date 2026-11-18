// Template: a screen's ViewModel with one StateFlow of a sealed UiState.
// Adjust to match project conventions:
//   - Route arguments: a SavedStateHandle in the constructor, read with `savedStateHandle.toRoute<…>()`.
//   - One-off events (a snackbar, navigating after a save): a Channel, a SharedFlow, or a state field?

package com.example.app.example

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed interface ExampleListUiState {
    data object Loading : ExampleListUiState

    data object Error : ExampleListUiState

    data object Empty : ExampleListUiState

    data class Success(
        val items: List<Example>,
        val isRefreshing: Boolean = false,
    ) : ExampleListUiState
}

@HiltViewModel
class ExampleListViewModel @Inject constructor(
    private val repository: ExampleRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow<ExampleListUiState>(ExampleListUiState.Loading)
    val uiState: StateFlow<ExampleListUiState> = _uiState.asStateFlow()

    private var loadJob: Job? = null

    init {
        load()
    }

    // Success keeps its items on screen while they reload; the other states show Loading.
    fun refresh() {
        _uiState.update { state ->
            if (state is ExampleListUiState.Success) state.copy(isRefreshing = true) else ExampleListUiState.Loading
        }
        load()
    }

    private fun load() {
        loadJob?.cancel()
        loadJob = viewModelScope.launch {
            val next = try {
                val items = repository.list()
                if (items.isEmpty()) ExampleListUiState.Empty else ExampleListUiState.Success(items)
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                ExampleListUiState.Error
            }
            _uiState.update { next }
        }
    }
}

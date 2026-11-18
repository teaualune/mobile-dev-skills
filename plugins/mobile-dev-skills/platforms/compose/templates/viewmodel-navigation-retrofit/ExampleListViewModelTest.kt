// Template: ViewModel tests: the state each scenario's WHEN leads to, and the calls it makes.
// They carry a scenario's `test` anchor when its THEN is about a request, saved data or an event,
// or when the project has no Robolectric; otherwise the screen's test carries it.
//
// Each test's name is the requirement id and the scenario title, exactly as the spec
// writes them, with the characters standards.md's "Form" lists (the id's `.`) written as `_`.
// The spec's `test` anchors point at that name.
//
// Adjust to match project conventions:
//   - Where do fakes live, and does the project use a mocking library (MockK, Mockito-Kotlin)?

package com.example.app.example

import app.cash.turbine.test
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import java.io.IOException

@OptIn(ExperimentalCoroutinesApi::class)
class ExampleListViewModelTest {
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    // The load that init starts waits on the test dispatcher until the test advances it.
    @Test
    fun `example-list_1 Loading`() = runTest {
        val viewModel = ExampleListViewModel(FakeExampleRepository(Result.success(emptyList())))

        assertEquals(ExampleListUiState.Loading, viewModel.uiState.value)
    }

    @Test
    fun `example-list_1 Error`() = runTest {
        val viewModel = ExampleListViewModel(FakeExampleRepository(Result.failure(IOException("offline"))))
        advanceUntilIdle()

        assertEquals(ExampleListUiState.Error, viewModel.uiState.value)
    }

    @Test
    fun `example-list_1 Empty`() = runTest {
        val viewModel = ExampleListViewModel(FakeExampleRepository(Result.success(emptyList())))
        advanceUntilIdle()

        assertEquals(ExampleListUiState.Empty, viewModel.uiState.value)
    }

    @Test
    fun `example-list_1 Success`() = runTest {
        val viewModel = ExampleListViewModel(FakeExampleRepository(Result.success(listOf(sample))))
        advanceUntilIdle()

        assertEquals(ExampleListUiState.Success(listOf(sample)), viewModel.uiState.value)
    }

    @Test
    fun `example-list_2 Retry`() = runTest {
        val repository = FakeExampleRepository(Result.failure(IOException("offline")))
        val viewModel = ExampleListViewModel(repository)
        advanceUntilIdle()
        repository.result = Result.success(listOf(sample))

        viewModel.uiState.test {
            assertEquals(ExampleListUiState.Error, awaitItem())
            viewModel.refresh()
            assertEquals(ExampleListUiState.Loading, awaitItem())
            assertEquals(ExampleListUiState.Success(listOf(sample)), awaitItem())
        }
        assertEquals(2, repository.listCalls)
    }
}

class FakeExampleRepository(var result: Result<List<Example>>) : ExampleRepository {
    var listCalls = 0
        private set

    override suspend fun list(): List<Example> {
        listCalls++
        return result.getOrThrow()
    }
}

private val sample = Example(id = "1", name = "First")

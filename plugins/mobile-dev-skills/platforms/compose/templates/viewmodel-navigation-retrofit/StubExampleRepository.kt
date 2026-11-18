// Template: a stub repository for when the backend API isn't ready yet.
// Use it when the spec marks the entity provisional. When the real API is ready:
//   1. Delete this file.
//   2. Bind RetrofitExampleRepository in ExampleModule again.
//   3. Remove the TODO(api) comments from the model.

package com.example.app.example

import kotlinx.coroutines.delay
import javax.inject.Inject

// TODO(api): delete this file when the real backend is ready.
class StubExampleRepository @Inject constructor() : ExampleRepository {
    override suspend fun list(): List<Example> {
        delay(400)
        return SAMPLES
    }

    private companion object {
        // TODO(api): replace with sample data matching the agreed shape
        val SAMPLES = emptyList<Example>()
    }
}

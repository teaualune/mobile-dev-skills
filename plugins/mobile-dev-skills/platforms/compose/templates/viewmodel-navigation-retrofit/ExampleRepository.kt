// Template: a repository interface and its Retrofit implementation.
// Adjust to match project conventions:
//   - Does the project map errors to its own type, or return a Result, instead of throwing?
//   - Is there a shared data source or API client to go through?

package com.example.app.example

import javax.inject.Inject

interface ExampleRepository {
    suspend fun list(): List<Example>
}

// Throws HttpException for a non-2xx status, IOException when the request fails,
// and SerializationException for a body that doesn't match the DTO.
class RetrofitExampleRepository @Inject constructor(
    private val api: ExampleApi,
) : ExampleRepository {
    // Retrofit's suspend calls are main-safe, so no dispatcher switch is needed.
    override suspend fun list(): List<Example> = api.list().items.map { it.toExample() }
}

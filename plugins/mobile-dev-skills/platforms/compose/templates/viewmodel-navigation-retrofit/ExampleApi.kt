// Template: a Retrofit interface with suspend functions.
// Adjust to match project conventions:
//   - Does the project return `Response<T>` or a result type instead of letting errors throw?

package com.example.app.example

import retrofit2.http.GET

interface ExampleApi {
    // No leading "/": it would drop the base URL's path.
    @GET("examples")
    suspend fun list(): ExamplePageDto
}

// Template: repository tests through the real Retrofit and converter, against MockWebServer.
//
// Named like the screen's tests; the words after the scenario title tell them apart.
//
// Adjust to match project conventions:
//   - Take the converter and the Json from where the app builds its Retrofit.
//   - Serve the JSON the spec gives for each endpoint.

package com.example.app.example

import kotlinx.coroutines.test.runTest
import mockwebserver3.MockResponse
import mockwebserver3.MockWebServer
import okhttp3.MediaType.Companion.toMediaType
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.fail
import org.junit.Before
import org.junit.Test
import retrofit2.HttpException
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory

class ExampleRepositoryTest {
    private val server = MockWebServer()
    private lateinit var repository: RetrofitExampleRepository

    @Before
    fun setUp() {
        server.start()
        val retrofit = Retrofit.Builder()
            .baseUrl(server.url("/"))
            .addConverterFactory(NetworkModule.provideJson().asConverterFactory("application/json".toMediaType()))
            .build()
        repository = RetrofitExampleRepository(retrofit.create(ExampleApi::class.java))
    }

    @After
    fun tearDown() {
        server.close()
    }

    @Test
    fun `example-list_1 Success maps the response`() = runTest {
        server.enqueue(MockResponse(body = """{"items":[{"id":"1","display_name":"First","rank":3}]}"""))

        val items = repository.list()

        assertEquals(listOf(Example(id = "1", name = "First")), items)
        assertEquals("/examples", server.takeRequest().url.encodedPath)
    }

    @Test
    fun `example-list_1 Error throws on a server error`() = runTest {
        server.enqueue(MockResponse(code = 500))

        try {
            repository.list()
            fail("Expected an HttpException")
        } catch (e: HttpException) {
            assertEquals(500, e.code())
        }
    }
}

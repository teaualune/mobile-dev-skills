// Template: Hilt bindings for the feature, and the app-wide network providers.
// Adjust to match project conventions:
//   - A project that already provides Retrofit keeps ExampleModule only.
//   - The base URL and the interceptors (auth, logging) come from where the project keeps them.

package com.example.app.example

import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
interface ExampleModule {
    // While the API is provisional, bind StubExampleRepository here instead.
    @Binds
    fun bindExampleRepository(repository: RetrofitExampleRepository): ExampleRepository

    companion object {
        @Provides
        fun provideExampleApi(retrofit: Retrofit): ExampleApi = retrofit.create(ExampleApi::class.java)
    }
}

// App-wide, only for a project without a Retrofit of its own: move it beside the app's other modules.
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton
    fun provideJson(): Json = Json { ignoreUnknownKeys = true }

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient = OkHttpClient.Builder().build()

    @Provides
    @Singleton
    fun provideRetrofit(client: OkHttpClient, json: Json): Retrofit =
        Retrofit.Builder()
            // Retrofit requires the trailing "/".
            .baseUrl("https://api.example.com/")
            .client(client)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
}

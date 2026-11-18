// Template: a @Serializable DTO and the domain model it maps to.
// Adjust to match project conventions:
//   - Does the project keep DTOs apart from its models, or decode into the models directly?
//   - Where does it map them: an extension like `toExample()`, or a mapper class?

package com.example.app.example

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

data class Example(
    val id: String,
    val name: String,
)

@Serializable
data class ExampleDto(
    val id: String,
    @SerialName("display_name") val displayName: String,
)

@Serializable
data class ExamplePageDto(
    val items: List<ExampleDto>,
)

fun ExampleDto.toExample(): Example = Example(id = id, name = displayName)

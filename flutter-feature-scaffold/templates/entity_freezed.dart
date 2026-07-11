// Template: Freezed + json_serializable entity
// Replace `Example` with the entity name, `example` with the snake_case file name.
// Run `dart run build_runner build --delete-conflicting-outputs` after generating.

import 'package:freezed_annotation/freezed_annotation.dart';

part 'example.freezed.dart';
part 'example.g.dart';

@freezed
class Example with _$Example {
  const factory Example({
    required String id,
    required String name,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    String? description,
  }) = _Example;

  factory Example.fromJson(Map<String, dynamic> json) => _$ExampleFromJson(json);
}

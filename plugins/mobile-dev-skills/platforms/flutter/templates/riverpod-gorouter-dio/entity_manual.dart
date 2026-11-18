// Template: Plain Dart entity without codegen.
// Use when the project does not use freezed/json_serializable.

class Example {
  final String id;
  final String name;
  final DateTime createdAt;
  final String? description;

  const Example({
    required this.id,
    required this.name,
    required this.createdAt,
    this.description,
  });

  factory Example.fromJson(Map<String, dynamic> json) {
    return Example(
      id: json['id'] as String,
      name: json['name'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      description: json['description'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'created_at': createdAt.toIso8601String(),
        if (description != null) 'description': description,
      };

  Example copyWith({
    String? id,
    String? name,
    DateTime? createdAt,
    String? description,
  }) {
    return Example(
      id: id ?? this.id,
      name: name ?? this.name,
      createdAt: createdAt ?? this.createdAt,
      description: description ?? this.description,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Example &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          name == other.name &&
          createdAt == other.createdAt &&
          description == other.description;

  @override
  int get hashCode => Object.hash(id, name, createdAt, description);
}

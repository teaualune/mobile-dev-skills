// Template: Stub repository for when the backend API is not ready yet.
//
// Use this when the spec marks the entity as PROVISIONAL.
// Implements the same interface as the real repository, but returns
// hardcoded sample data with simulated latency.
//
// When the real API is ready:
//   1. Delete this file.
//   2. Swap the provider to point at the real repository.
//   3. Remove the // TODO(api) comments from the entity.

import 'example.dart';
import 'example_repository.dart';

/// Stub implementation used while the backend API is not yet available.
///
/// TODO(api): delete this file when the real backend is ready.
class StubExampleRepository implements ExampleRepository {
  StubExampleRepository();

  // Hardcoded sample data — adjust fields to match the provisional entity shape.
  static final _samples = <Example>[
    // TODO(api): replace with realistic sample data matching the agreed shape
  ];

  @override
  Future<List<Example>> list({int page = 1, int pageSize = 20}) async {
    await Future<void>.delayed(const Duration(milliseconds: 400));
    return _samples;
  }

  @override
  Future<Example> getById(String id) async {
    await Future<void>.delayed(const Duration(milliseconds: 300));
    final found = _samples.where((e) => e.id == id).toList();
    if (found.isEmpty) {
      throw Exception('Stub: no example with id $id');
    }
    return found.first;
  }

  @override
  Future<Example> create({required String name, String? description}) async {
    await Future<void>.delayed(const Duration(milliseconds: 400));
    throw UnimplementedError(
      'Stub: create() not implemented. Backend API not ready yet.',
    );
  }

  @override
  Future<void> delete(String id) async {
    await Future<void>.delayed(const Duration(milliseconds: 300));
    throw UnimplementedError(
      'Stub: delete() not implemented. Backend API not ready yet.',
    );
  }
}

// NOTE: For the above to work, `ExampleRepository` must be an abstract class
// or interface with the same method signatures. If your project's repository
// classes are concrete, refactor to:
//
//   abstract class ExampleRepository {
//     Future<List<Example>> list({int page, int pageSize});
//     // ...
//   }
//
//   class HttpExampleRepository implements ExampleRepository { ... }
//   class StubExampleRepository implements ExampleRepository { ... }
//
// Then the provider chooses between them.

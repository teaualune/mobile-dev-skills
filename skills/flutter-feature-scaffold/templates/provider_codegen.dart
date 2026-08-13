// Template: Riverpod with riverpod_annotation (code-gen).
// Assumes project uses riverpod_generator. Run build_runner after generating.
//
// Adjust the dio provider import — most projects already have a shared one
// (often in lib/core/network/ or lib/src/network/). Do NOT define a new dio
// provider here if one exists.

import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../data/example_repository.dart';
import '../data/example.dart';
// import '../../../core/network/dio_provider.dart'; // <-- match project path

part 'example_providers.g.dart';

@riverpod
ExampleRepository exampleRepository(ExampleRepositoryRef ref) {
  final dio = ref.watch(dioProvider); // assumes shared dioProvider exists
  return ExampleRepository(dio);
}

@riverpod
Future<List<Example>> examples(ExamplesRef ref) async {
  final repo = ref.watch(exampleRepositoryProvider);
  return repo.list();
}

@riverpod
class ExampleController extends _$ExampleController {
  @override
  FutureOr<void> build() {}

  Future<void> create({required String name, String? description}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final repo = ref.read(exampleRepositoryProvider);
      await repo.create(name: name, description: description);
      ref.invalidate(examplesProvider);
    });
  }

  Future<void> remove(String id) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final repo = ref.read(exampleRepositoryProvider);
      await repo.delete(id);
      ref.invalidate(examplesProvider);
    });
  }
}

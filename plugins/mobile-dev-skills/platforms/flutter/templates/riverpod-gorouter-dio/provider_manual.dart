// Template: Riverpod without code-gen (plain flutter_riverpod).

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/example_repository.dart';
import '../data/example.dart';
// import '../../../core/network/dio_provider.dart'; // <-- match project path

final exampleRepositoryProvider = Provider<ExampleRepository>((ref) {
  final dio = ref.watch(dioProvider); // assumes shared dioProvider exists
  return ExampleRepository(dio);
});

final examplesProvider = FutureProvider<List<Example>>((ref) async {
  final repo = ref.watch(exampleRepositoryProvider);
  return repo.list();
});

class ExampleController extends AsyncNotifier<void> {
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

final exampleControllerProvider =
    AsyncNotifierProvider<ExampleController, void>(ExampleController.new);

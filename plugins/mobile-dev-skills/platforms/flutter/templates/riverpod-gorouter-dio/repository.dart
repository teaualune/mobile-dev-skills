// Template: Repository using Dio.
// Adjust to match project conventions:
//   - Does the project use a Result<T> / Either type, or just throw?
//   - Is there an existing base ApiClient that wraps Dio?
//   - How are errors mapped (custom exception types)?

import 'package:dio/dio.dart';

import 'example.dart';

class ExampleRepository {
  ExampleRepository(this._dio);

  final Dio _dio;

  Future<List<Example>> list({int page = 1, int pageSize = 20}) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        '/examples',
        queryParameters: {'page': page, 'page_size': pageSize},
      );
      final items = (res.data?['items'] as List<dynamic>? ?? []);
      return items
          .map((e) => Example.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      // TODO: map to project's exception type
      throw Exception('Failed to load examples: ${e.message}');
    }
  }

  Future<Example> getById(String id) async {
    try {
      final res = await _dio.get<Map<String, dynamic>>('/examples/$id');
      return Example.fromJson(res.data!);
    } on DioException catch (e) {
      throw Exception('Failed to load example $id: ${e.message}');
    }
  }

  Future<Example> create({required String name, String? description}) async {
    try {
      final res = await _dio.post<Map<String, dynamic>>(
        '/examples',
        data: {
          'name': name,
          if (description != null) 'description': description,
        },
      );
      return Example.fromJson(res.data!);
    } on DioException catch (e) {
      throw Exception('Failed to create example: ${e.message}');
    }
  }

  Future<void> delete(String id) async {
    try {
      await _dio.delete<void>('/examples/$id');
    } on DioException catch (e) {
      throw Exception('Failed to delete example $id: ${e.message}');
    }
  }
}

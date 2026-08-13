// Template: ConsumerWidget screen with AsyncValue.when().
//
// Adjust to match project conventions:
//   - Does the project have shared LoadingView / ErrorView / EmptyView widgets?
//     If yes, use them instead of the inline ones below.
//   - What's the project's theme accessor (AppColors, Theme.of(context), etc.)?
//   - Does it use a custom AppBar wrapper?

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../application/example_providers.dart';
import '../data/example.dart';

class ExampleListScreen extends ConsumerWidget {
  const ExampleListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final examplesAsync = ref.watch(examplesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Examples')),
      body: RefreshIndicator.adaptive(
        onRefresh: () async => ref.invalidate(examplesProvider),
        child: examplesAsync.when(
          loading: () => const _LoadingView(),
          error: (err, _) => _ErrorView(
            error: err,
            onRetry: () => ref.invalidate(examplesProvider),
          ),
          data: (items) {
            if (items.isEmpty) return const _EmptyView();
            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, i) => _ExampleTile(item: items[i]),
            );
          },
        ),
      ),
    );
  }
}

class _ExampleTile extends StatelessWidget {
  const _ExampleTile({required this.item});
  final Example item;

  @override
  Widget build(BuildContext context) {
    // Extract a local so it promotes — never use the `!` operator.
    final description = item.description;
    return ListTile(
      title: Text(item.name),
      subtitle: description != null ? Text(description) : null,
      onTap: () {
        // TODO: navigate to detail via go_router
        // context.go('/examples/${item.id}');
      },
    );
  }
}

class _LoadingView extends StatelessWidget {
  const _LoadingView();
  @override
  Widget build(BuildContext context) =>
      const Center(child: CircularProgressIndicator());
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.error, required this.onRetry});
  final Object error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48),
            const SizedBox(height: 12),
            Text(
              'Something went wrong',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(
              '$error',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}

class _EmptyView extends StatelessWidget {
  const _EmptyView();
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.inbox_outlined, size: 48),
            const SizedBox(height: 12),
            Text(
              'Nothing here yet',
              style: Theme.of(context).textTheme.titleMedium,
            ),
          ],
        ),
      ),
    );
  }
}

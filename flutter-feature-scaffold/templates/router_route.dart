// Template: go_router route entries.
//
// Most projects centralize routes in lib/router/app_router.dart (or similar).
// Add these GoRoute entries to that file's existing route list, do NOT create
// a new GoRouter instance.
//
// If the project uses typed routes (@TypedGoRoute), follow that pattern
// instead of the plain version below.

import 'package:go_router/go_router.dart';

import '../presentation/example_list_screen.dart';
import '../presentation/example_detail_screen.dart';

// Plain GoRoute version
final exampleRoutes = <GoRoute>[
  GoRoute(
    path: '/examples',
    name: 'examples',
    builder: (context, state) => const ExampleListScreen(),
    routes: [
      GoRoute(
        path: ':id',
        name: 'example_detail',
        builder: (context, state) {
          final id = state.pathParameters['id']!;
          return ExampleDetailScreen(id: id);
        },
      ),
    ],
  ),
];

// Typed-route version (only if project uses @TypedGoRoute):
//
// @TypedGoRoute<ExamplesRoute>(
//   path: '/examples',
//   routes: [TypedGoRoute<ExampleDetailRoute>(path: ':id')],
// )
// class ExamplesRoute extends GoRouteData {
//   const ExamplesRoute();
//   @override
//   Widget build(BuildContext context, GoRouterState state) =>
//       const ExampleListScreen();
// }
//
// class ExampleDetailRoute extends GoRouteData {
//   const ExampleDetailRoute({required this.id});
//   final String id;
//   @override
//   Widget build(BuildContext context, GoRouterState state) =>
//       ExampleDetailScreen(id: id);
// }

#!/bin/bash
# Fixture for the trigger suite: a small Flutter app with one spec, its index, an intake sheet and a build script.
set -euo pipefail

mkdir -p lib/features/articles lib/core test/features/articles docs/specs .mobile-dev-skills/saved-articles scripts

cat > pubspec.yaml <<'EOF'
name: news_reader
description: A news reader app.
publish_to: none
version: 2.3.1+57
# android: 112 = 2.3.1

environment:
  sdk: ">=3.4.0 <4.0.0"

dependencies:
  flutter:
    sdk: flutter
  flutter_riverpod: ^2.5.1
  go_router: ^14.2.0
  dio: ^5.4.3

dev_dependencies:
  flutter_test:
    sdk: flutter
  mocktail: ^1.0.3
  flutter_lints: ^4.0.0

flutter:
  uses-material-design: true
EOF

cat > lib/main.dart <<'EOF'
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'router.dart';

void main() => runApp(const ProviderScope(child: NewsApp()));

class NewsApp extends StatelessWidget {
  const NewsApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp.router(routerConfig: router);
}
EOF

cat > lib/router.dart <<'EOF'
import 'package:go_router/go_router.dart';

import 'features/articles/article_detail_screen.dart';

final router = GoRouter(routes: [
  GoRoute(path: '/articles/:id', builder: (context, state) => ArticleDetailScreen(id: state.pathParameters['id'] ?? '')),
]);
EOF

cat > lib/features/articles/article_card.dart <<'EOF'
import 'package:flutter/material.dart';

class ArticleCard extends StatelessWidget {
  const ArticleCard({super.key, required this.title, required this.summary});

  final String title;
  final String summary;

  @override
  Widget build(BuildContext context) => Card(
        child: Row(children: [
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          Text(summary),
        ]),
      );
}
EOF

cat > lib/features/articles/article_detail_screen.dart <<'EOF'
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ArticleDetailScreen extends ConsumerWidget {
  const ArticleDetailScreen({super.key, required this.id});

  final String id;

  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
        appBar: AppBar(title: const Text('Article')),
        body: Center(child: Text('Article $id')),
      );
}
EOF

cat > lib/core/date_utils.dart <<'EOF'
String relativeDate(DateTime date, DateTime now) {
  final days = now.difference(date).inDays;
  if (days == 0) return 'today';
  if (days == 1) return 'yesterday';
  return '$days days ago';
}
EOF

cat > test/features/articles/saved_articles_screen_test.dart <<'EOF'
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('saved-articles.1 Empty', (tester) async {});
  testWidgets('saved-articles.1 Success', (tester) async {});
}
EOF

cat > docs/specs/saved-articles-spec.md <<'EOF'
# Saved articles

> Last verified: 2026-10-02 (commit 1a2b3c4)

## 1. Summary
Users bookmark an article from its detail screen and find it later in a Saved tab.

## 6. Behavior

### Requirement: Saved list
<!-- id: saved-articles.1 -->
<!-- screen: SavedArticlesScreen -->
<!-- entities: SavedArticle -->
<!-- enforced: lib/features/saved/saved_articles_screen.dart#SavedArticlesScreen -->

#### Scenario: Empty
<!-- test: test/features/articles/saved_articles_screen_test.dart#saved-articles.1 Empty -->
- WHEN the user has saved nothing
- THEN the screen shows "No saved articles yet"

#### Scenario: Success
<!-- test: test/features/articles/saved_articles_screen_test.dart#saved-articles.1 Success -->
- WHEN the user has saved articles
- THEN the screen lists them, newest first

## Changelog

### Update 2026-10-20
- Saved articles now sync across devices for signed-in users.

### Addendum: offline
- The saved list is cached and shown offline, with a banner.
EOF

cat > docs/specs/comments-spec.md <<'EOF'
# Comments

> Last verified: (filled in Phase 2)

## 1. Summary
Readers comment on an article and reply to a comment.

## 6. Behavior

### Requirement: Comment list
<!-- id: comments.1 -->
<!-- screen: CommentsScreen -->
<!-- entities: Comment -->
<!-- enforced: (filled in Phase 2) -->

#### Scenario: Empty
<!-- test: (filled in Phase 2) -->
- WHEN the article has no comments
- THEN the screen shows "Be the first to comment"
EOF

cat > docs/specs/index.md <<'EOF'
| Spec | Feature | Status | Last verified |
|---|---|---|---|
| [saved-articles-spec.md](saved-articles-spec.md) | Saved articles | implemented | 2026-10-02 |
| [comments-spec.md](comments-spec.md) | Comments | approved | — |
EOF

mkdir -p .mobile-dev-skills/reading-history
cat > .mobile-dev-skills/reading-history/intake.md <<'EOF'
## Summary
Every article a user opens is recorded; a History tab lists them by day.
## Routes
/history (new tab)
## Affected screens
ArticleDetailScreen: records the visit on open.
## Entities & APIs
HistoryEntry { articleId, openedAt }; stored locally, no API.
## Binding logic
Grouped by day, newest first; swipe to delete an entry; "Clear all" asks for confirmation.
## Figma references
None
EOF

cat > .mobile-dev-skills/saved-articles/intake.md <<'EOF'
## Summary
Bookmark articles from the detail screen; a Saved tab lists them.
## Routes
/saved (new tab), /articles/:id (existing)
## Affected screens
ArticleDetailScreen: adds a bookmark icon.
## Entities & APIs
SavedArticle { id, articleId, savedAt }; GET/POST/DELETE /me/saved-articles
## Binding logic
Optimistic toggle; the list is newest first.
## Figma references
None
EOF

cat > scripts/build-version.sh <<'EOF'
#!/bin/bash
# Project config — ADAPT
APP_NAME="News Reader"
echo "build-version.sh stub"
EOF
chmod +x scripts/build-version.sh

git init -q
git add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -qm "fixture"

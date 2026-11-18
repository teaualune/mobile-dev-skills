---
description: A layout bug fix; no spec work.
expected_outcome: No plugin skill fires in any state.
tags: [negative]
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
---
Fix the RenderFlex overflow in lib/features/articles/article_card.dart when the title is long.

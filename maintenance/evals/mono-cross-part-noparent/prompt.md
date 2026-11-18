---
description: The same cross-part request in a monorepo without a project workflow for it.
expected_outcome: Neither feature-intake nor feature-workflow fires.
tags: [monorepo, negative-plugin]
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
---
Add followed topics across the product: the backend stores which topics each user follows (new endpoints), the web dashboard gets a page to follow and unfollow topics, and the mobile app gets a Topics screen to follow them and filters the feed by them.

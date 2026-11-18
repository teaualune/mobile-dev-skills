---
description: A feature spanning backend, web and app in a monorepo whose project has its own cross-part workflow.
expected_outcome: Neither feature-intake nor feature-workflow fires. The eval loads only the plugin's skills, so the project's cross-part-feature skill is a file the model may read, not a listed skill.
tags: [monorepo, negative-plugin]
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
---
Add followed topics across the product: the backend stores which topics each user follows (new endpoints), the web dashboard gets a page to follow and unfollow topics, and the mobile app gets a Topics screen to follow them and filters the feed by them.

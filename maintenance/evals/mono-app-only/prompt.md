---
description: An app-only feature in the monorepo, using endpoints that already exist.
expected_outcome: feature-intake fires, and no other plugin skill does.
tags: [monorepo, positive, feature-intake]
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
---
In the mobile app, add a Topics screen where the user follows or unfollows topics, using the backend's GET /v1/topics and PUT /v1/me/topics endpoints, which are already live.

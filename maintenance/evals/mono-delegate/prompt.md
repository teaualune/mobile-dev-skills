---
description: A delegation brief handed over for the app's part of a cross-part feature.
expected_outcome: feature-workflow fires.
tags: [monorepo, positive, feature-workflow]
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
---
The backend and web parts of followed topics are specced. Hand the app's part to the mobile feature workflow with this delegation brief:

# Delegation brief — Followed topics
- Slug: followed-topics
- From: the project's `cross-part-feature` skill
- Request: new feature
- App: app/
- Specs: app/docs/specs/
- API contract: backend/docs/specs/articles.md (approved)
- Approval: here

## App slice
A Topics screen, opened from the article list, lists every topic with a follow switch; the feed shows only followed topics when the user follows at least one.

## Other parts
- backend: `GET /v1/topics`, `PUT /v1/me/topics`
- web: a page to follow and unfollow topics

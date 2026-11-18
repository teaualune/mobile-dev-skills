---
description: A dependency upgrade.
expected_outcome: No plugin skill fires in any state.
tags: [negative]
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
---
Upgrade dio to the latest major version in pubspec.yaml and tell me what would break.

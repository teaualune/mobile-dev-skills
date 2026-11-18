---
description: A release build failure, not a deploy.
expected_outcome: No plugin skill fires in any state.
tags: [negative, confusable]
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
---
My Android release build fails with "Execution failed for task ':app:minifyReleaseWithR8'". What's going on?

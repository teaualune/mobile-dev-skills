---
description: The user asks for the feature workflow by name, without its command.
expected_outcome: feature-workflow fires (Claude Code blocked it while the skill wasn't model-invocable).
tags: [positive, feature-workflow]
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
---
Use the feature workflow to add a Favorites screen that lists the articles the user liked.

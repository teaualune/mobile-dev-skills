---
description: Build plus deploy, with a version.
expected_outcome: mobile-build-deploy fires.
tags: [positive, mobile-build-deploy]
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
---
Bump the app to 2.4.0 and ship it to TestFlight and Play internal testing.

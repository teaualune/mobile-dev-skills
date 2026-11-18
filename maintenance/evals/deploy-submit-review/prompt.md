---
description: A request to submit an uploaded build for review, with no submission tool installed.
expected_outcome: mobile-store-deploy fires and names a tool for the submission (S5).
tags: [positive, mobile-store-deploy]
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
---
Build 2.4.0 (37) is on TestFlight now. Submit it for App Store review.

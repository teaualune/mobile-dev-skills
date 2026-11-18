---
description: Deploy-only of an existing archive.
expected_outcome: mobile-store-deploy fires.
tags: [positive, mobile-store-deploy]
max_turns: 8
timeout_seconds: 240
allowed_tools: [Read, Glob, Grep, Skill]
---
The iOS archive is already built at build/ios/archive/Runner.xcarchive. Upload it to TestFlight.

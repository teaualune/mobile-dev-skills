---
name: feature-intake
description: "Gather the requirements for a new or changed feature in a mobile app, before any spec or code — the user wants to add a feature, describes one they're planning, or hands over a requirements dump. Asks targeted follow-ups for what's missing. Not for a monorepo feature that also needs backend or web work. Do NOT use to write the spec (feature-spec) or code (feature-scaffold)."
---

# Feature Intake

Drive the conversation that turns a fuzzy feature idea into complete requirements. The output of this skill is a fully-populated **Intake Sheet**, saved as `.mobile-dev-skills/<feature-slug>/intake.md` ("Saving the sheet"). That sheet then feeds `feature-spec`.

## The Intake Sheet — 6 sections

Every feature needs answers to all six. Track which are filled and which are gaps.

```
1. SUMMARY
   - Feature name:
   - One-sentence purpose:
   - User-facing outcome:
   - Trigger / entry points:
   - Out of scope (including non-functional topics that don't apply, each with its reason):

2. ROUTES (new screens)
   For each new screen:
   - Screen name:
   - Route path (or route name, depending on the project's routing library):
   - Purpose:
   - Navigation in (where the user arrives from, including deep links and notification taps):
   - Navigation out (where they go next):
   - Route params / extra:

3. AFFECTED EXISTING SCREENS
   For each affected screen:
   - Screen name / file:
   - What changes (new button, new section, new state, etc.):
   - Why:

4. ENTITIES & APIS
   For each new entity:
   - Entity name:
   - Fields (name + type + nullable):
   - Source: API response | local | derived
   For each new endpoint:
   - HTTP method + path:
   - Request shape:
   - Response shape:
   - Auth required?:
   - Error cases to handle:
   For each native interface (platform code the feature needs that no package in the project provides):
   - Name and purpose:
   - Platforms:
   - Methods (arguments, result, errors, and anything the platform sends back later):

5. BINDING LOGIC
   - State primitives needed (match the project's state-management library, e.g. Riverpod providers, Blocs/Cubits, ChangeNotifiers, GetX controllers, MobX stores):
   - Data flow (API → repository → state primitive → screen):
   - Side effects (analytics events with their parameters, navigation, snackbars, dialogs):
   - Caching / invalidation rules:
   - Offline, background and resume behavior:
   - Permissions & capabilities (which ones, on which platforms, when they're requested, the usage-string wording, what happens on denial):
   - Platform differences (what behaves differently per platform, e.g. iOS and Android, and why):
   - Loading / error / empty / success state behavior per screen:
   - Rules that always hold (limits, ordering, consistency across screens):

6. FIGMA REFERENCES
   - Frame links or attached screenshots:
   - Specific design tokens called out (spacing, color, typography):
   - Reused components vs new components:
   - Any motion / animation specs:
   - Accessibility (screen-reader labels, tap targets, text scaling):
   - Copy & localization (languages, where new strings go, date and number formats):
```

## Saving the sheet

- **Path:** `.mobile-dev-skills/<feature-slug>/intake.md` at the project root (the folder holding the platform's manifest, e.g. `pubspec.yaml`; in a monorepo, the app's folder, not the repository's root). The slug is the feature name in lowercase ASCII kebab-case (an English rendering for a non-Latin name). It is chosen once: the spec's requirement ids reuse it, and so does the spec file's name where the project names specs by feature. For a change to an existing feature, take it from the spec's ids, or, if the spec has no ids, from its file name without the project's naming affixes (e.g. `-feature-spec`). A project that has only the pre-rename `.flutter-skills/` keeps its sheets there: use that folder wherever this skill says `.mobile-dev-skills/`. When both exist, use `.mobile-dev-skills/`, unless the old folder holds unfinished work (an `intake.md` without a `> Spec:` or `> Split:` first line, a `tasks.md` with unticked tasks, or a `request.md` or `brief.md` whose feature's spec has no index row yet): then name it and ask which folder to use.
- **Write it** as soon as the feature name is known and the saved sheets are checked (below), and update it in the same turn an answer fills or changes a field. Keep the six sections and their field names. An unanswered field stays empty; one the user defers says `TBD`; one that doesn't apply, such as a part of the app a change leaves alone, says `N/A` (a non-functional topic that doesn't apply goes under out of scope instead, with its reason).
- **Finished sheets.** Whoever writes the spec from the sheet adds `> Spec: <spec path>` as its first line. A sheet that `feature-workflow` splits into sub-features gets `> Split: <sub-slug>, …` there instead, and each sub-feature gets a sheet of its own. A sheet with either line is finished, since its spec or its sub-features' sheets hold everything it said: a later change to the feature starts a new sheet in its place. A sheet without either is unfinished: resume from it, reflecting back what it holds, then ask about its first empty field.

## How to run intake

### In a monorepo: the app's part only

The app is one part of a monorepo when the project root isn't the repository's root (`git rev-parse --show-toplevel`) and another folder of the repository holds a part of its own, with its own manifest or specs (`feature-workflow`'s "State files"). There, a request that also needs work another part owns, such as an endpoint that doesn't exist yet or a web page, isn't gathered here: name the parts it touches, from the request and the repository's top-level folders, point to the project's own workflow for features that span parts when one is listed, and write nothing. Without one, offer to gather the app's part alone, with the other parts out of scope. A request that only uses what another part already provides is the app's own, and so is one that comes with a delegation brief (`feature-workflow`'s "Delegated runs").

### First: look for a saved sheet

Before the first question and before writing anything, list the saved sheets, `.mobile-dev-skills/*/intake.md` at the project root, and read the first line and Summary of each. Say what you found in one line: `Saved sheets: <slug> (unfinished), <slug> (finished)`, or `Saved sheets: none`.

- An unfinished sheet for this feature (the same slug, or a Summary that describes it) → resume it as "Finished sheets" above says. Never start a new sheet over it.
- An unfinished sheet that may be this feature → ask whether to resume it or to start a separate feature with a slug of its own.
- A finished sheet for this feature → start a new sheet in its place.
- A sheet written from a delegation brief (a `brief.md` beside it) is unfinished like any other: resume it. Its out-of-scope field already names the other parts' work; ask only about the app's part.

Then go on with the matching section below.

### When the user starts with a dump (text file or long message)

1. Read the entire input first. Do not ask any questions yet.
2. Extract every piece of info that maps to a section above. Populate the Intake Sheet.
3. Reflect back what you got — 5-8 bullet points, neutral language, no embellishment.
4. List the gaps explicitly: "I still need: <X>, <Y>, <Z>."
5. Ask about the **single highest-priority gap** first. Priority order: Routes → Entities/APIs → Binding → Affected screens → Figma → Non-functional topics → Summary polish.

### When the user starts with a short description ("I want to add notifications")

1. Acknowledge briefly.
2. Ask about **Summary + Routes** together — this is the natural opener.
3. Proceed section by section. Don't jump ahead.

### General rules during intake

- **One question per turn** unless two are so tightly coupled that splitting feels weird (e.g. "what's the route path, and is it nested under an existing shell?").
- **Reflect before advancing.** When the user answers, restate it in one line before asking the next thing. This catches misunderstandings cheap.
- **Probe for the forgotten things.** After the user describes a screen, always ask about: loading state, error state, empty state, pull-to-refresh, pagination. After they describe an API, ask about: auth, error codes, retry behavior. After a permission: when it's asked for, the usage string, and what the user sees after a denial. These get skipped 90% of the time.
- **Don't invent — with one exception.** If the user says "the API returns user data" without specifying fields, ask. Never guess `{id, name, email}` and move on. **Exception:** if the user explicitly tells you the backend API isn't ready yet but the UI work needs to proceed, you may propose a provisional entity shape. Treat this as a collaborative sketch, not a unilateral decision:
  1. Propose the shape with brief reasoning ("Based on the screen needing a title, body, and timestamp, I'd suggest `Article { id, title, body, publishedAt }` — does that match what you expect from the backend?").
  2. Ask the user to sanity-check it before treating it as decided.
  3. Mark the entity in the Intake Sheet as `PROVISIONAL` so the spec and scaffold steps know to add TODO comments and use a stub repository.
  4. Add the provisional shape to a tracked list of "things to confirm with backend later".

  Shapes taken from another part's spec that isn't approved yet (a delegation brief's `draft` API contract) are `PROVISIONAL` the same way, copied from that spec rather than proposed.
- **Figma last, unless the user leads with it.** Visual details are easier once the data shape is clear. When the user gives Figma frame links, no tool in the session reads Figma files directly (a Figma MCP server, for one) but the Claude-in-Chrome tools are there, and a `figma-design-to-artifact` skill is listed, offer to export the frames with it into `.mobile-dev-skills/<feature-slug>/figma/`; the Figma references then name the exported files beside the links.

### Non-functional topics

Before intake is done, go through these topics. Ask only about the relevant ones not already answered, one per turn as usual, and record each answer in the field the table names. Topics recorded in the same field can share one question.

| Topic | Relevant when the feature… | Record in |
|---|---|---|
| Offline / poor network | loads or sends data | Binding logic: offline, background and resume |
| Deep links | adds a screen that could open from a link, a notification or a share | Routes: navigation in |
| Permissions | uses the camera, photos, location, microphone, contacts, notifications or similar, or needs a capability such as a background mode or an entitlement | Binding logic: permissions & capabilities |
| Native code & platform differences | needs platform code that no package in the project provides (a native SDK, a sensor, Bluetooth, platform UI), or behaves differently per platform | Entities & APIs: native interfaces; Binding logic: platform differences |
| Analytics events | has user actions or outcomes the product tracks | Binding logic: side effects |
| Accessibility | adds or changes UI | Figma references: accessibility |
| Localization | adds user-visible text, dates, numbers or prices | Figma references: copy & localization |
| Background / resume | shows data that can go stale, or runs timers, uploads, playback or long requests | Binding logic: offline, background and resume |
| Push notifications | sends, receives or opens from a push | Summary: entry points; Routes: navigation in; Binding logic: side effects |

- **Don't ask about a topic that clearly doesn't apply.** Record it under Summary's out-of-scope field with the reason (e.g. "Push notifications — not affected, no server events"), as you do a topic the user explicitly cuts; the user sees both in the spec. A topic the user wants to settle later is a TBD, not out of scope.
- **Existing practice is an answer.** When the project already handles a topic (ARB files, a shared offline banner), propose that practice by name and ask for a yes or a correction.
- **Changing an existing feature:** only the topics the change touches.

## Reflecting back — example

User dumps a paragraph about a "saved articles" feature.

Good reflection:
> Here's what I picked up:
> - **Feature**: Saved articles — users can bookmark articles to read later.
> - **New screen**: 1 (Saved Articles list).
> - **Affected**: Article detail screen gets a bookmark icon in the app bar.
> - **API**: Implied but not specified — I'll need the endpoints.
> - **Entity**: `SavedArticle` (or reuse `Article`?) — also unclear.
>
> Gaps: API endpoints + shapes, entity model decision, pagination behavior, what happens when the list is empty.
>
> Let's start with the API — what endpoints does the backend expose for save/unsave/list?

Bad reflection:
> Got it! That sounds like a great feature. So you want users to save articles, view them later, and have a nice UI for it. Should we start coding?

The bad one invents nothing-statements ("great feature"), summarizes without surfacing gaps, and jumps to code.

## When intake is done

You're done when all six sections are populated with concrete answers or `N/A` (not placeholders like "TBD") and every non-functional topic (for a change, every one it touches) is answered or under out of scope, OR the user explicitly marks remaining gaps as "leave as TBD in the spec, we'll resolve later."

Then hand off to `feature-spec`, pointing it at the saved sheet. When `feature-workflow` invoked this skill, return to it instead: its Step 1.4 comes before the spec.

## Anti-patterns

- Asking 10 questions in one message.
- Running the non-functional topics as a questionnaire, including ones that clearly don't apply.
- Accepting vague answers ("just normal error handling") without probing.
- Letting the user skip the Binding section because it feels tedious — this is where bugs come from.
- Inventing API field names to keep the conversation moving (unless the user has explicitly said the API isn't ready and asked for provisional shapes — in which case, propose openly and get sanity-checked).
- Starting to design widget trees or view hierarchies mid-intake. That's Phase 2.

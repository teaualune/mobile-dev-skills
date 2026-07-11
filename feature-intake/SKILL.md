---
name: feature-intake
description: Use this skill whenever the user wants to add a new feature to a Flutter app, describe a feature they're planning, or hand over a requirements dump (text file or long message) for a feature. Triggers on phrases like "I want to add", "new feature", "let me describe this feature", "here's the spec", or any time feature requirements are being gathered before code is written. This skill drives the interactive requirement-gathering conversation — extracting what's present, identifying what's missing, and asking targeted follow-ups. Do NOT use this skill for writing the spec document itself (use flutter-feature-spec) or generating code (use flutter-feature-scaffold).
---

# Feature Intake

Drive the conversation that turns a fuzzy feature idea into complete requirements. The output of this skill is a fully-populated **Intake Sheet** stored in conversation memory or as `intake.md` in the working directory. That sheet then feeds `flutter-feature-spec`.

## The Intake Sheet — 6 sections

Every feature needs answers to all six. Track which are filled and which are gaps.

```
1. SUMMARY
   - Feature name:
   - One-sentence purpose:
   - User-facing outcome:
   - Trigger / entry points:

2. ROUTES (new screens)
   For each new screen:
   - Screen name:
   - Route path (or route name, depending on the project's routing library):
   - Purpose:
   - Navigation in (where the user arrives from):
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

5. BINDING LOGIC
   - State primitives needed (match the project's state-management library — Riverpod providers, Blocs/Cubits, ChangeNotifiers, GetX controllers, MobX stores, etc.):
   - Data flow (API → repository → state primitive → screen):
   - Side effects (analytics, navigation, snackbars, dialogs):
   - Caching / invalidation rules:
   - Loading / error / empty state behavior per screen:

6. FIGMA REFERENCES
   - Frame links or attached screenshots:
   - Specific design tokens called out (spacing, color, typography):
   - Reused components vs new components:
   - Any motion / animation specs:
```

## How to run intake

### When the user starts with a dump (text file or long message)

1. Read the entire input first. Do not ask any questions yet.
2. Extract every piece of info that maps to a section above. Populate the Intake Sheet.
3. Reflect back what you got — 5-8 bullet points, neutral language, no embellishment.
4. List the gaps explicitly: "I still need: <X>, <Y>, <Z>."
5. Ask about the **single highest-priority gap** first. Priority order: Routes → Entities/APIs → Binding → Affected screens → Figma → Summary polish.

### When the user starts with a short description ("I want to add notifications")

1. Acknowledge briefly.
2. Ask about **Summary + Routes** together — this is the natural opener.
3. Proceed section by section. Don't jump ahead.

### General rules during intake

- **One question per turn** unless two are so tightly coupled that splitting feels weird (e.g. "what's the route path, and is it nested under an existing shell?").
- **Reflect before advancing.** When the user answers, restate it in one line before asking the next thing. This catches misunderstandings cheap.
- **Probe for the forgotten things.** After the user describes a screen, always ask about: loading state, error state, empty state, pull-to-refresh, pagination. After they describe an API, ask about: auth, error codes, retry behavior. These get skipped 90% of the time.
- **Don't invent — with one exception.** If the user says "the API returns user data" without specifying fields, ask. Never guess `{id, name, email}` and move on. **Exception:** if the user explicitly tells you the backend API isn't ready yet but the UI work needs to proceed, you may propose a provisional entity shape. Treat this as a collaborative sketch, not a unilateral decision:
  1. Propose the shape with brief reasoning ("Based on the screen needing a title, body, and timestamp, I'd suggest `Article { id, title, body, publishedAt }` — does that match what you expect from the backend?").
  2. Ask the user to sanity-check it before treating it as decided.
  3. Mark the entity in the Intake Sheet as `PROVISIONAL` so the spec and scaffold steps know to add TODO comments and use a stub repository.
  4. Add the provisional shape to a tracked list of "things to confirm with backend later".
- **Figma last, unless the user leads with it.** Visual details are easier once the data shape is clear.

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

You're done when all six sections are populated with concrete answers (not placeholders like "TBD"), OR the user explicitly marks remaining gaps as "leave as TBD in the spec, we'll resolve later."

Then hand off to `flutter-feature-spec`.

## Anti-patterns

- Asking 10 questions in one message.
- Accepting vague answers ("just normal error handling") without probing.
- Letting the user skip the Binding section because it feels tedious — this is where bugs come from.
- Inventing API field names to keep the conversation moving (unless the user has explicitly said the API isn't ready and asked for provisional shapes — in which case, propose openly and get sanity-checked).
- Starting to design Flutter widget trees mid-intake. That's Phase 2.

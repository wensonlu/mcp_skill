---
name: ios-incremental-sync
description: Use when Dog Project needs to watch or classify H5, React Native, Capacitor, or iOS changes and choose the cheapest safe sync path - decides between H5 cap copy, RN bundle generation, and native iOS rebuild prompts
---

# iOS Incremental Sync

## Overview

Use the cheapest safe action after code changes. H5 changes only copy Capacitor web output, RN JavaScript changes only regenerate the RN bundle, and possible native changes escalate to an explicit iOS rebuild decision.

Core rule: when unsure whether a dependency/config change can affect native code, classify it as `native-build`.

## Decision Table

| Change | Paths | Action |
|---|---|---|
| H5-only | `frontend/src/**`, `frontend/public/**`, `frontend/index.html`, `frontend/vite.config.js`, Tailwind/PostCSS config | `cd frontend && pnpm build && npx cap copy ios` |
| RN JS-only | `rn-app/App.js`, `rn-app/index.js`, `rn-app/src/**`, `rn-app/assets/**`, `rn-app/app.json` | `cd rn-app && pnpm bundle:ios` |
| Native-impact | `frontend/ios/**`, `frontend/capacitor.config.json`, `frontend/package.json`, `frontend/pnpm-lock.yaml`, `rn-app/package.json`, `rn-app/pnpm-lock.yaml`, `rn-app/ios/**`, `rn-app/android/**` | Prompt for deliberate native rebuild |

Ignore generated outputs when classifying: `frontend/dist/**`, `frontend/ios/App/App/public/**`, `frontend/ios/App/App/rn_bundle/**`, `rn-app/dist/**`, `node_modules/**`.

## Mixed Changes

Run actions in this order:

1. H5 changed: `cd frontend && pnpm build && npx cap copy ios`
2. RN JS changed: `cd rn-app && pnpm bundle:ios`
3. Native changed: report why native rebuild is needed; do not silently run Xcode unless the user asked for automatic rebuild.

Examples:

| Changed together | Actions |
|---|---|
| H5 + RN JS | H5 copy, then RN bundle |
| H5 + Native | H5 copy, then native rebuild prompt |
| RN JS + Native | RN bundle, then native rebuild prompt |

## Native Rebuild Prompt

When `native-build` is detected, explain the triggering path(s) and recommend:

```bash
cd frontend/ios/App
pod install
xcodebuild -workspace App.xcworkspace -scheme App -configuration Debug -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 17' CODE_SIGNING_ALLOWED=NO -quiet build
```

Only run this command automatically when the user explicitly asks to rebuild native iOS.

## Watch Script

Use the bundled script for repeatable classification and optional execution:

```bash
node skills/ios-incremental-sync/scripts/ios-incremental-sync.mjs --dry-run --changed frontend/src/pages/Home.jsx
node skills/ios-incremental-sync/scripts/ios-incremental-sync.mjs --dry-run --since HEAD
node skills/ios-incremental-sync/scripts/ios-incremental-sync.mjs --watch
```

When installed inside Dog Project as `.agents/skills/ios-incremental-sync`, use that directory in the command instead. The script resolves the Git repository from the current working directory; set `IOS_INCREMENTAL_SYNC_ROOT=/path/to/dog_project` when launching it from another directory.

`--watch` polls `git status`, debounces by snapshot, ignores generated outputs, and prevents concurrent sync runs. It executes H5/RN actions but only prints the native rebuild recommendation.

## Common Mistakes

- Do not use `cap sync ios` for H5-only changes; prefer `cap copy ios` to avoid unnecessary plugin/pod work.
- Do not treat `package.json` or lockfile changes as JS-only; dependency changes can affect native autolinking.
- Do not trigger from generated output paths; that causes build loops.
- Do not run RN bundle for pure H5 changes.

---
name: ship
description: >-
  Ship current Git work end-to-end. In an Eve project, ensure changed agent
  behavior has real session-based Eve eval coverage, bootstrap functional evals
  when missing, and run the local eval gate before commit; then create a feature
  branch, scoped commit, push, PR, call the project babysit skill, merge, sync
  the default branch, and give a safe-exit verdict. Use when the user runs
  /ship or explicitly asks to ship, land, merge, or publish current repository
  changes.
---

# /ship — Eve functional evals through merge, then safe-exit

Run the full ship pipeline for the current repo or worktree, then declare this chat safe to close. Treat text following `/ship` as an optional user note.

Reuse an installed `babysit` or equivalent PR-readiness skill when available; do not run two competing readiness loops. Search project-level skill directories first (`.agents/skills`, `.claude/skills`, `.cursor/skills`, `.pi/skills`), then the current agent's user-level skill directory. If none exists, use the bounded fallback in step 5.

Follow user git safety rules (no force-push to main/master, no amend unless conditions permit it, no `--no-verify` unless asked, never update git config). Prefer `gh` for GitHub and the repository's host-native CLI elsewhere. Follow the user's language and project rules.

## Preflight

1. Detect repo root (`git rev-parse --show-toplevel`). If not a git repo, stop and say so.
2. Resolve and fetch the intended base/default branch, then inspect `git status -sb`, unstaged/staged diffs, `git log -5 --oneline`, upstream tracking, ahead/behind, and commits in `origin/<base>..HEAD`.
3. Inspect the open PR and all PR history for the current head branch, including each PR's `baseRefName`. A squash-merged branch remains non-ancestral to the base, so a nonempty `origin/<base>..HEAD` range alone does not prove work is unshipped. If no PR is open, decide in this priority order:
   1. If any same-head PR targeting the intended `<base>` is `MERGED` and its recorded `headRefOid` equals `HEAD`, treat that exact head as already shipped. Ignore matching PRs merged into other bases. This intended-base match is conclusive; do not let `git cherry` override it.
   2. Only when no exact intended-base merged-PR match exists, run `git cherry origin/<base> HEAD`. If it contains no `+` commits, every patch is already equivalent upstream, so treat the head as shipped.
   3. If neither check proves the work shipped, continue the pipeline. If history or patch evidence is ambiguous, stop rather than create a duplicate PR.
4. Note secrets risk (`.env`, credentials, tokens). **Do not commit secrets** unless this repo's contract explicitly allows it.
5. State the plan in one short block before mutating git or remote state.

Declare **nothing to ship** only when the tree is clean, this branch has no open PR, and either `origin/<base>..HEAD` has no task commits or the checks above prove those commits already landed on the intended base. A clean branch with genuinely unshipped commits still has work to ship.

When there is nothing to ship, skip steps 0–5, synchronize or verify the local default branch as required by step 6, then emit the step 7 safe-exit verdict. Do not open another PR.

## Pipeline (do in order; do not skip)

### 0) Eve functional eval coverage and local gate (before first commit)

Run before staging or committing ship work. This step has two jobs: add missing functional coverage for changed Eve behavior, then execute that coverage. Fix failures and re-run until green; do not commit while evals are red.

#### 0a) Detect an Eve project without installing anything

Treat the current app or workspace package as Eve-backed when repository evidence shows one of these:

- `package.json` declares `eve` in dependencies or devDependencies
- the lockfile or workspace manifest resolves an `eve` package used by this app
- an Eve agent filesystem exists (`agent/agent.ts`, `agent/instructions.*`, or the app's equivalent Eve agent root)
- a local Eve binary or installed package exists (`node_modules/.bin/eve` or resolvable `node_modules/eve`)

Do not use bare `npx eve ...` as detection because it may download a package. If evidence is absent, skip step 0 and record `not an Eve project`. A `.cursor/skills/eve` file alone is guidance, not proof that the application runs Eve.

When Eve is present, resolve its installed package and read `node_modules/eve/docs/README.md`, then the relevant `docs/evals/` guides before authoring eval code. Installed docs match the project's version.

#### 0b) Audit coverage against the diff

Inspect `evals/evals.config.ts`, every relevant `*.eval.ts`, package scripts, CI eval commands, and changed agent behavior. Map each user-visible behavior in the diff to an eval that drives the real Eve session protocol.

Behavior changes needing direct coverage include instructions, tools, skills, connections, channels, subagents, schedules, HITL, structured output, session continuity, and agent-facing HTTP behavior. Pure docs, formatting, generated files, or internal refactors with unchanged behavior do not require a new eval, though the existing gate still runs.

Existing eval files are not enough by themselves. If changed behavior has no meaningful assertion, add or update a targeted eval before shipping.

#### 0c) Bootstrap functional evals when absent or insufficient

If the Eve project has no eval suite:

1. Create `evals/evals.config.ts` with `defineEvalConfig({})`.
2. Create at least one focused `evals/<behavior>.eval.ts` using `defineEval`.
3. Ensure TypeScript includes `evals/**/*.ts` when project config requires an explicit include.
4. Add package scripts only when the project uses package scripts and lacks an eval entry. Prefer `evals:run: eve eval` and `evals:ci: eve eval --strict --junit .eve/junit.xml`, adapted to the project's package manager and conventions.

A functional eval must send a realistic user turn through Eve (`t.send`, `t.start`, or an attached target), then assert observable behavior. Minimum useful gate: `t.succeeded()` plus one behavior-specific assertion. Examples:

- changed tool: prompt that requires it, `t.calledTool("tool_name")`, and output/reply check
- changed skill: prompt that requires it, `t.loadedSkill("skill-name")`, and result check
- conversation behavior: user-like prompt plus `t.messageIncludes(...)` or deterministic `t.check(...)`
- session memory: two turns and a continuity assertion
- HITL or side effect: name and use the Eve session driver APIs, not a prose-only “send and approve” plan. A typical flow is `const parked = await t.send(...)`, `parked.parked()`, `const request = t.requireInputRequest(...)`, `parked.notCalledTool(...)`, `await t.respond(...)`, `t.succeeded()`, then `t.calledTool(...)` with test input/output matchers. Adapt exact methods to installed Eve docs.

For any write, payment, refund, deletion, message-send, or other external side effect, prove isolation before running the approved path: bind the tool to a mock/stub, sandbox, dry-run adapter, or dedicated test backend and test resource. Never let an eval call the production side-effecting backend. Assert both halves of the boundary: the tool is not called before approval, then the isolated tool is called with expected test input after approval.

Do not create placeholder evals that only import successfully, grep source, check files, or assert a generic greeting unrelated to the changed behavior. Follow existing tags, helpers, naming, and target conventions instead of inventing a parallel suite.

If no model credentials or required service are available, `eve eval --list` or typecheck only proves discovery, not functionality. Keep shipping blocked until the functional eval runs against an approved local or remote target, unless the user explicitly accepts skipping that gate.

#### 0d) Validate discovery, then run the gate

After adding or changing eval files, first list/discover them with the project's local Eve command, then run the narrow changed eval before the broader PR gate. Use an installed/local binary or existing script; avoid package-download side effects.

Choose commands from the user note first, then repository conventions and diff scope:

| Situation | Command |
|-----------|---------|
| User names tier, tag, IDs, or target URL | Use exactly that scope with the project's local Eve command |
| Newly added or changed eval | local `eve eval <id-or-group> --strict` first |
| Existing project PR/CI eval script | run that exact script |
| Generic Eve project without a project gate | local `eve eval --strict` |
| win-agent-os default PR gate | `SUITE_START_CHAT_SURFACE=0 npm run evals:ci` |
| win-agent-os full local smoke | `SUITE_START_CHAT_SURFACE=0 npm run evals:smoke` |
| win-agent-os faster iteration | `SUITE_START_CHAT_SURFACE=0 npm run evals:fast` |
| Pre-merge confidence or user asks for full | project full-eval script, such as `npm run evals:full` |

After adding or changing eval files, run the repository's catalog generator when one exists, such as:

```bash
npm run evals:catalog
```

Include tracked generated catalog output in the same commit (`docs/play-all-features/eval-catalog.md` in win-agent-os).

On MBA or any machine other than macmini, always set `SUITE_START_CHAT_SURFACE=0` for win-agent-os; `/ship` must not start local Next/Eve surfaces forbidden by `AGENTS.md`. Other projects follow their own machine rules.

On failure, inspect `.eve/evals/<timestamp>/` artifacts, fix code or evals, and re-run. Never weaken assertions or CI workflows merely to pass. For debug fixes in win-agent-os, also follow `docs/cursor-debug-mode-evals.md`.

### 1) Branch safety — before committing

- If currently on the default branch with task changes, create and switch to a feature branch **before** staging or committing.
- If task commits already exist on the local default branch, first preserve them on a feature branch; only then realign the local default ref with `origin/<default>`. Never force-push the default branch.
- Keep unrelated dirty files out of the feature branch commit.

### 2) Commit (if needed)

- Stage only relevant files for this task, not unrelated dirty or runtime files.
- Draft a concise commit message (why over what); match recent log style.
- Commit via HEREDOC. If a hook fails, fix it and make a **new** commit; do not amend unless amend rules permit it.

### 3) Push

- Run `git push -u origin HEAD` or equivalent. Never force-push protected default branches.

### 4) Pull request or merge request

- If no open review exists for this head, create one with Summary + Test plan, including the Eve eval command and result from step 0.
- If one exists, reuse it and push new commits onto the same branch.
- Record its stable number or URL. Pass that identifier explicitly to every later host CLI command, even after switching branches.
- Report the review URL.

### 5) Make the review merge-ready

If a `babysit` or equivalent project/user skill exists, load and follow it exactly with the saved review identifier, then return here. Otherwise use this fallback:

1. Inspect mergeability, required checks, unresolved review threads, and in-scope bot findings with the host-native CLI/API.
2. Resolve clear conflicts and scoped defects. Never weaken CI merely to pass.
3. After any code fix, re-run step 0 locally, commit, push, and re-check the same review.
4. Repeat until **mergeable + required checks green + comments triaged**, or until an irreducible human decision is required.

Do not mix the installed skill and fallback loop. If branch and base intent conflict, stop and ask the user. Remote CI eval lanes are the server-side counterpart to step 0; local evals should pass before push so readiness work is not wasted on avoidable failures.

### 6) Merge

- When step 5 reports merge-ready, merge with the saved review identifier and host-native CLI; prefer the repository's normal merge method and delete the remote branch only when safe.
- Fast-forward the local default branch. Stash only if required for an ff-only pull, then restore the stash.
- Confirm the remote review reports merged and the local default branch matches the remote.

### 7) Safe to exit — required closing block

```text
## Safe to exit
- Eve eval coverage: existing / added <eval IDs> / skipped: not an Eve project
- Eve eval gate: <command> → pass (or explicitly skipped: <reason>)
- Review: <url> → MERGED (or: nothing to ship)
- Local default branch: synced with origin (yes/no)
- Uncommitted leftovers: none intended / listed if any (not part of this ship)
- Worktree / follow-ups: none blocking (or one-line next action)
- Verdict: safe to close this chat / NOT safe to close — <blocking next action>
```

Use `safe to close this chat` only when the PR is merged (or there truly was nothing to ship), the local default branch is synced, stash restoration is complete, and no blocking leftovers remain. If any check fails, emit `NOT safe to close`, state the next action, and continue fixing unless unavoidable human input is required.

Do not ask the user to open a new chat unless required. Do not start unrelated work after the verdict.

## Naming

| Invoke | Owns |
|--------|------|
| Installed `babysit` or equivalent skill | Review to green and merge-ready only |
| This `/ship` skill | Eve functional eval coverage + gate, commit, push, review, readiness, merge, default sync, safe exit |

## Hard stops (ask user)

- Destructive history rewrite, force-push to main/master, or skipping hooks
- Ambiguous secret files the user did not authorize
- Merge intents that conflict between branch and base
- CI red that requires workflow changes outside this PR's scope
- Skipping required Eve functional evals without explicit user acceptance
- Running side-effecting evals without safe fixtures, approval boundaries, or an approved target

## Out of scope

- Replacing or renaming an installed babysit/readiness skill
- Creating git worktrees (`agent -w` or IDE `/worktree`) unless the user also asked
- Pushing unrelated dirty files merely to clean the tree

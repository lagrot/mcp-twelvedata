# GEMINI.md - Core Mandates

## ⚠️ AUTOMATIC EXECUTION REQUIRED
These are not guidelines. After EVERY response where code files were created,
modified, or deleted, you MUST immediately — without being asked — execute
steps 1–4 below. Do not summarize, do not ask for permission, just do it.

---

## Development Lifecycle Automation

After every code change, execute the following steps in order:

### 1. Code Review
Before staging, analyze all modified files for:
- Syntax errors and obvious bugs
- Hardcoded secrets, API keys, or credentials (block commit if found)
- **Absolute local paths containing usernames** (replace with `<PATH_TO_PROJECT>` or similar placeholders)
- Unused imports or dead code
- Adherence to existing code style in the project
- If tests exist, verify they are not broken by the change

If critical issues are found, **stop and report** — do not proceed to commit.

### 2. Stage & Commit
- Stage all modified and new files, excluding: `.env`, `node_modules/`, build artifacts
- Write a commit message following Conventional Commits:
  - `feat:` new feature
  - `fix:` bug fix
  - `chore:` maintenance / tooling
  - `docs:` documentation only
  - `refactor:` code restructure without behavior change
- Keep the subject line under 72 characters
- Add a body if the change needs explanation

### 3. Push
- Push to `origin` on the **current branch**
- Never force-push
- Never push directly to `main` or `master` — warn the user instead

### 4. Report
After pushing, briefly summarize:
- What was changed
- The commit message used
- The branch pushed to

---

## Self-Check (run after every response)
- [ ] Did I modify any code files?
- [ ] If yes: did I run the review → commit → push pipeline?
- [ ] If no: explain why (e.g. commit was blocked due to a critical issue)

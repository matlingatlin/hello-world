---
description: Run all three test suites and the typecheck, and report the real numbers
---

Run every suite in this repo and report what actually happened.

```bash
# Engine — Python, ~3.5 minutes. Run it first and in the background if you can;
# it is by far the slowest.
apps/engine/.venv/bin/python -m pytest -q

# API — NestJS + Prisma, in-process
cd apps/api && npx vitest run

# App — React
cd apps/app && npx vitest run

# Typecheck across every workspace ("lint" here is tsc --noEmit)
pnpm -r lint
```

Report the counts each suite prints — passed, failed, skipped — and the exit
status of the typecheck.

Two rules about reporting, both learned the hard way in this repo:

- **Read the exit code of the command you meant.** A suite piped into `tail`
  reports `tail`'s status, not pytest's. A green summary was once reported here
  while a guardrail test was failing, because of exactly that.
- **A red suite is a red suite.** Say which test failed and paste its output.
  Do not round up, do not describe a failure as flakiness without evidence, and
  do not proceed to commit.

Expected as of 2026-08-26: engine 655 passed / 6 skipped, api 135, app 109,
typecheck clean. A number lower than these without an explanation means tests
were lost, not that the suite got faster.

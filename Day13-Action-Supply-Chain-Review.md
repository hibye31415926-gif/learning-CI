# Day 13 — Action Supply Chain Review

## 1. Review Scope

- Repository: `github.com/hibye31415926-gif/learning-CI`
- Reviewed Branch: all remote branches (`main`, `feature/day2-pr-ci`, `feature/day3-checkout`, `ci/day4-event-lab`, `ci/day5-lab`, `day6-dag-lab` … `day12-negative-test`)
- Current HEAD Commit SHA: `d6b886b16e047e001c057e4517897b7799aeb4d1` (main)
- Workflow File: every file under `.github/workflows/`
- Review Date: 2026-11-18
- Review Mode: **Static** (Dynamic verification: not performed)

## 2. Action Inventory

Method: `git grep -n -E 'uses:' <ref> -- .github/workflows` across all remote branches.

| Workflow File | Branch | Action Reference | Classification |
| ------------- | ------ | ---------------- | -------------- |
| `day3.yml` | `feature/day3-checkout` | `actions/checkout@v7` | GitHub-owned / Tag |
| `day5-python-ci.yml` | `ci/day5-lab` | `actions/checkout@v6` | GitHub-owned / Tag |
| `day5-python-ci.yml` | `ci/day5-lab` | `actions/setup-python@v7` | GitHub-owned / Tag |
| `day6-dag-lab.yml` | `day6-dag-lab` | `actions/checkout@v4` (used twice) | GitHub-owned / Tag |
| `day7-matrix-lab.yml` | `day7-matrix-lab` | `actions/checkout@v6` | GitHub-owned / Tag |
| `day7-matrix-lab.yml` | `day7-matrix-lab` | `actions/setup-python@v6` | GitHub-owned / Tag |
| `day8-cache-artifact-lab.yml` | `day8-cache-artifact-lab` | `actions/checkout@v6` | GitHub-owned / Tag |
| `day8-cache-artifact-lab.yml` | `day8-cache-artifact-lab` | `actions/setup-python@v6` | GitHub-owned / Tag |
| `day8-cache-artifact-lab.yml` | `day8-cache-artifact-lab` | `actions/upload-artifact@v4` | GitHub-owned / Tag |
| `day8-cache-artifact-lab.yml` | `day8-cache-artifact-lab` | `actions/download-artifact@v5` | GitHub-owned / Tag |
| `day9-diagnosis-lab.yml` | `day9-reports-lab` | `actions/checkout@v6` | GitHub-owned / Tag |
| `day9-diagnosis-lab.yml` | `day9-reports-lab` | `actions/setup-python@v6` | GitHub-owned / Tag |
| `day9-diagnosis-lab.yml` | `day9-reports-lab` | `actions/upload-artifact@v4` | GitHub-owned / Tag |
| `day11-least-privilege.yml` | `day11-least-privilege-lab` | `actions/checkout@v7` | GitHub-owned / Tag |
| `day11-least-privilege.yml` | `day11-least-privilege-lab` | `actions/setup-python@v7` | GitHub-owned / Tag |
| `day11-least-privilege.yml` | `day11-least-privilege-lab` | `actions/upload-artifact@v7` | GitHub-owned / Tag |
| `day11-least-privilege.yml` | `day11-least-privilege-lab` | `actions/download-artifact@v8` | GitHub-owned / Tag |

Notes:
- `main.yml`, `day12-secrets-lab.yml`, `day4-event-lab.yml`, `day10-concurrency-lab.yml` contain **no** `uses:` (all `run:`).
- No **Third-party** actions, no **Local** actions, and no **Reusable Workflows** currently exist in this repository.
- Because no third-party action exists, `dorny/test-reporter@v2` is reviewed as a **candidate** (Section 3B).

## 3. Selected Actions

### 3A. In-repo action (deep review): `actions/checkout@v7`

- Upstream Repository: `https://github.com/actions/checkout`
- Maintainer / Owner: `actions` (GitHub) — repo not archived, ~9.0k stars
- Current Reference: `@v7` (Tag)
- Resolved Full Commit SHA: `3d3c42e5aac5ba805825da76410c181273ba90b1`
- Release / Source Evidence: same SHA observed in the live Day 11 runner log (`actions/checkout@v7 (SHA:3d3c42e…)`) — tag resolution matches what actually executed.

### 3B. Candidate third-party action (static review): `dorny/test-reporter@v2`

- Upstream Repository: `https://github.com/dorny/test-reporter`
- Maintainer / Owner: `dorny` (Michal Dorner) — not archived, ~1.2k stars
- Current Reference: `@v2` (Tag)
- Resolved Full Commit SHA: `df6247429542221bc30d46a036ee47af1102c451`

## 4. Source Code Review

| Check | Finding | Evidence |
| ----- | ------- | -------- |
| `action.yml` / `action.yaml` | `actions/checkout@v7`: `runs: using: node24, main: dist/index.js, post: dist/index.js` | fetched at pinned SHA `3d3c42e…` |
| Runtime and scripts | Bundled JS (`dist/index.js`); no inline shell in `action.yml`. Source is compiled → review `src/` of the upstream repo for behaviour. |  |
| External downloads | None declared in `action.yml`. No `curl \| bash` pattern. |  |
| Network behaviour | Git fetch/push over HTTPS/SSH to the target repository only. |  |
| Dependencies | Bundled into `dist/`; not resolved at runtime. |  |
| Token / Secrets handling | Input `token` defaults to `${{ github.token }}`; `persist-credentials` defaults to **true**. We set `persist-credentials: false` in `day11-least-privilege.yml`. | input definitions |
| `action.yml` (candidate) | `dorny/test-reporter@v2`: `runs: using: node20, main: dist/index.js`; input `token` default `${{ github.token }}`; outputs a **check run** `conclusion`. | fetched at `df62474…` |
| Candidate risk | Requires `checks: write` to create a check run; bundles `src/`+`dist/`+`package-lock.json`. Not currently used in this repo. |  |

## 5. Workflow Trust Boundary

| Area | Finding |
| ---- | ------- |
| Trigger | Lab workflows use `push` (branch-scoped), `pull_request`, or `workflow_dispatch`. `pull_request:` in `day11` has **no** `branches:` filter (broad). |
| Runner Type | GitHub-hosted only (`ubuntu-latest`, `windows-latest`). No self-hosted runners → no persistent host state/credentials. |
| GITHUB_TOKEN Permissions | Measured (Day 11 run log): `test` = `Contents: read` + `Metadata: read`; `summarize` = `Metadata: read` only. `day12` uses `permissions: {}`. |
| Secrets Injected | Only `day12-secrets-lab.yml` (a **fake** environment secret, scoped to `day12-lab-staging`). No real credentials anywhere. |
| Untrusted Input Exposure | Lab runs originate from same-repo branches. **Fork PR behaviour was not tested.** |
| Additional Risks | All actions are **tag-pinned** (movable); `day8` still on older majors (`upload-artifact@v4`, `download-artifact@v5`). `main` has no branch protection. |

## 6. Risk Assessment

- Severity: **Medium** — every action is GitHub-owned (reputable), but all are pinned to movable tags and one workflow triggers broadly.
- Confidence: High for inventory, tag→SHA resolution, and permissions (measured from live run logs). Medium for source behaviour (bundled `dist/`, not line-by-line read).
- Confirmed Findings:
  1. All references use **mutable tags**, not immutable SHAs → ref-movement risk.
  2. `actions/download-artifact@v5` (day8) and older `upload-artifact@v4` remain in use.
  3. `day11-least-privilege.yml` triggers on **all** PR bases (no `branches:` filter).
- Advisory scan (GitHub Advisory Database, `ecosystem=actions`):

  | Advisory | Severity | Affected package | Range | Patched | Applicable to us? |
  | -------- | -------- | ---------------- | ----- | ------- | ----------------- |
  | GHSA-cxww-7g56-2vh6 | high | `actions/download-artifact` | >= 4.0.0, < 4.1.3 | 4.1.3 | **No** — we use v5 and v8 |
  | GHSA-5xr6-xhww-33m4 | high | `dawidd6/action-download-artifact` | < 6 | 6 | **No** — different package, not used |
  | GHSA-vqf5-2xx6-9wfm | high | `github/codeql-action` | 3.26.11–3.28.2 | 3.28.3 | **No** — not used |

  Key lesson: advisory matching must be by **exact package + version range**. The `download-artifact` name resemblance is a trap — ours (v5/v8) is patched.
- Unknowns: fork-PR trust boundary untested; no dynamic run of a pinned workflow; bundled `dist/` code not read line-by-line; no global advisory sweep of every version in use.
- Recommended Mitigations: pin all actions to verified full SHAs; upgrade day8 to current majors; add `branches: [main]` to the PR trigger; enable branch protection + required checks.

## 7. Final Decision

Decision: **Approve with conditions** (GitHub-owned actions) / **Hold** (candidate third-party action)

Reasoning:
- GitHub-owned actions (`actions/*`) come from a reputable owner, resolve to the expected SHAs, and no applicable advisories were found → acceptable to keep using, **conditional on** pinning to full SHAs.
- `dorny/test-reporter` is **not** approved for adoption yet: it needs `checks: write` and consumes a token. Hold until its source is read and permissions are scoped, then pin to a verified SHA.
- No action is rejected.

## 8. Verification Evidence

- Source File and Line: `.github/workflows/*.yml` `uses:` lines (see Section 2)
- Resolved SHAs:
  - `actions/checkout@v4` → `11d5960a326750d5838078e36cf38b85af677262`
  - `actions/checkout@v6` → `d23441a48e516b6c34aea4fa41551a30e30af803`
  - `actions/checkout@v7` → `3d3c42e5aac5ba805825da76410c181273ba90b1`
  - `actions/setup-python@v6` → `ece7cb06caefa5fff74198d8649806c4678c61a1`
  - `actions/setup-python@v7` → `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0`
  - `actions/upload-artifact@v4` → `ea165f8d65b6e75b540449e92b4886f43607fa02`
  - `actions/upload-artifact@v7` → `cf430e030ddbb5b0abf93d22962f4752f3646cd9`
  - `actions/download-artifact@v5` → `634f93cb2916e3fdff6788551b99b062d0335ce0`
  - `actions/download-artifact@v8` → `9000827ccba6bdab643e8b6fd33ac0654aef8333`
  - `dorny/test-reporter@v2` → `df6247429542221bc30d46a036ee47af1102c451`
- Review Links: `https://github.com/actions/checkout`, `https://github.com/actions/setup-python`, `https://github.com/actions/upload-artifact`, `https://github.com/actions/download-artifact`, `https://github.com/dorny/test-reporter`
- CI Run URL (executed evidence): `.../actions/runs/44146101562` (Day 11) — runner log showed resolved SHAs matching the table above.
- CI Result: success
- What Remains Unverified: fork-PR behaviour; dynamic run after SHA-pinning; line-by-line reading of bundled `dist/`.

## 9. Next Actions

1. Pin every `uses:` to a verified full 40-character SHA (start with `main`/`day11`).
2. Add `branches: [main]` to `day11-least-privilege.yml`'s `pull_request` trigger; upgrade `day8` to current action majors.
3. Before adopting any third-party action (e.g. `dorny/test-reporter`), complete a source read + explicit `permissions:` scoping, then pin it.

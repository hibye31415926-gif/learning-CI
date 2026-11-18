# Day 14 — PR Threat Model

## 1. Scope

- Project: Event Seat Reservation System
- Analysis Type: **Simulation** (Lab scenario Workflow A / Workflow B) **+ Repository Review** (real repo)
- Repository: `github.com/hibye31415926-gif/learning-CI`
- Commit SHA: `d6b886b16e047e001c057e4517897b7799aeb4d1` (main); all remote branches also scanned
- Workflow Files Reviewed: every file under `.github/workflows/` on all remote branches
- Assumptions:
  - The simulation assumes Workflow B is policy-allowed and its checkout protections are relaxed (as the Lab states). It is a **deliberately unsafe teaching case** and is **not** present in this repository.
  - The real-repo assessment is **read-only**; no malicious PR and no real credential exposure was performed.

## 2. Protected Assets

| Asset ID | Asset | Why It Matters | Impact if Compromised |
| -------- | ----- | -------------- | --------------------- |
| AS-01 | Repository integrity (`main` code) | Anything merged ships to all users | Supply-chain poisoning, backdoor |
| AS-02 | Credentials (`GITHUB_TOKEN`, staging credentials) | Grants write access / staging access | Unauthorized writes, credential theft |
| AS-03 | CI infrastructure (runners) | Runners hold credentials and network access | Lateral movement into internal network |
| AS-04 | Booking / customer data | Business + legal exposure | Data breach, reputational damage |

## 3. Threat Actors & Entry Points

| Actor | Controlled Input | Trust Level |
| ----- | ---------------- | ----------- |
| TA-01 External contributor | PR files: workflows, scripts, tests, dependency manifests | **Untrusted** |
| TA-02 Compromised / malicious third-party action | Code executed by CI | **Untrusted** |
| TA-03 Insider maintainer | Everything (PRs, settings, workflow edits) | Trusted |

Entry points considered: Pull Request Files, Dependency Manifest, Workflow Events (`pull_request_target`), Build Scripts, Test Scripts, Uploaded Artifacts.
Not every entry point is a vulnerability — the question is whether attacker-controlled content is **actually executed**.

## 4. Trust Boundaries

- **Untrusted → Execution**: contributor PR code must not be *executed* in a privileged context.
- **Execution → Credentials**: a job that runs untrusted code must not hold write tokens or secrets.
- **Events → Context**: `pull_request` runs with a read-only token and no secrets for forks; `pull_request_target` runs in the **base** repo context with the base token and secrets — crossing this boundary with untrusted code is the classic "Pwn Request".
- **Runner → Host**: self-hosted runners may retain state/credentials and reach internal networks; GitHub-hosted runners are ephemeral.
- **Artifact → Consumer**: artifacts produced by a low-trust job must not be *executed* by a high-trust job.

## 5. Attack Paths

### 5A. Simulation (Workflow B: `pull_request_target` + self-hosted + `contents: write` + staging secret + checkout PR head)

**AP-01 — PR code executed in a privileged context**
- Threat Actor: TA-01 External contributor
- Entry Point: `pull_request_target` trigger
- Execution: workflow checks out the **PR head** and runs tests → attacker script executes
- Required Conditions: `pull_request_target`; checkout of PR head; job holds `contents: write` + staging secret; self-hosted runner
- Permissions: `contents: write`, staging credential
- Protected Asset: AS-02 (credentials), AS-01 (repo)
- Potential Impact: secret exfiltration; attacker pushes malicious commits
- Likelihood: **High** · Severity: **High**

**AP-02 — Malicious dependency during install**
- Threat Actor: TA-01
- Entry Point: dependency manifest modified in the PR
- Execution: CI installs PR-provided dependencies → malicious install hook runs
- Required Conditions: CI installs PR-controlled dependencies; job holds write token
- Permissions: `contents: write`
- Protected Asset: AS-01 (repo)
- Potential Impact: supply-chain poisoning
- Likelihood: **Medium** · Severity: **High**

### 5B. Real repository assessment (this repo)

Static, read-only scan across all branches for `pull_request_target`, `workflow_run`, `runs-on:`, `secrets.`, `head.sha`, `permissions:`:

| Observation | Finding | Risk |
| ----------- | ------- | ---- |
| `pull_request_target` | **Not used anywhere** | None |
| `workflow_run` | **Not used anywhere** | None |
| Runners | All GitHub-hosted (`ubuntu-latest`; matrix ubuntu+windows) — **no self-hosted** | Low |
| Secrets | Only `day12-secrets-lab.yml` — an **environment-scoped fake** secret | Low |
| `head.sha` | Only an `echo` in `day4-event-lab.yml` (informational, not a checkout ref) | Low |
| Permissions | Declared (read-only) in all workflows; `day11` includes a `permissions: {}` job; `day12` uses `permissions: {}` | Low |
| Branch protection on `main` | **None** | Medium (no enforced gate) |
| Action pinning | All GitHub-owned but **tag-pinned** | Medium |

Conclusion: the highest-severity pattern (`pull_request_target` + privileged checkout of PR head) is **absent**. The realistic residual concerns are the **absence of a merge gate** and **tag-pinned actions** (see §9).

## 6. Proposed Mitigations

| Attack Path | Control | Rationale | Trade-off |
| ----------- | ------- | --------- | --------- |
| AP-01 | Use `pull_request` (never `pull_request_target` for untrusted code); set `permissions: contents: read`; no secrets in PR-triggered jobs; use GitHub-hosted runners | Fork PRs get a read-only token, no secrets, and never run in the base context | Fork PRs cannot write; not needed for tests |
| AP-02 | Pin/lock dependencies (`--require-hashes`, lock files); restrict install sources; no write token in the PR job | Malicious dependency code cannot execute or gain privilege | Extra dependency-management overhead |
| Both (defence in depth) | Workflow separation: untrusted test job (no secrets) vs privileged deploy job triggered only on `push` to `main`, gated by a Protected Environment with required reviewers | Privileged steps never run untrusted code | Slower deploys; more workflows |
| Both | Branch protection + required status checks on `main` | Turns CI from advisory into an enforced gate | Requires admin config; may block fast merges |

Additional question — would these controls break normal CI?
- Removing `contents: write`: unit tests only need read → no breakage (verified in Day 11 where `contents: read` was sufficient).
- No secrets in PR jobs: PR tests use no secrets → no breakage.
- Only deployment needs write/secrets → move to a separate `push`-triggered workflow.

## 7. Verification Plan

| Control | Verification Method | Expected Evidence | Result |
| ------- | ------------------- | ----------------- | ------ |
| Untrusted PR cannot use a write token | Check trigger + job permissions | Workflow YAML | **Verified (repo)**: all workflows declare read-only permissions |
| PR tests do not get deployment secrets | Check `secrets.` refs + environments | Workflow / Settings | **Verified (repo)**: only `day12` uses a fake env-scoped secret |
| Untrusted PR code is not run in a privileged job | Check checkout ref + executed commands | Workflow code review | **Verified (repo)**: no `pull_request_target`, no PR-head checkout in privileged context |
| Runner suits the trust level | Check runner labels / isolation | Runner config | **Verified (repo)**: all GitHub-hosted |
| Merge gate enforced | Check branch protection / required checks | Settings | **Not Verified**: `main` is not protected |
| Actions immutable | Check refs resolve to full SHAs | Workflow YAML / Day 13 review | **Not Verified**: still tag-pinned |

## 8. Residual Risks

1. **No branch protection / required checks** on `main` → CI is advisory, not an enforced gate.
2. **Tag-pinned actions** → ref-movement / supply-chain risk (Day 13).
3. **Fork-PR behaviour untested** — conclusions rely on static analysis and simulation.
4. **Bundled action code not read line-by-line** → behaviour trust is partly reputation-based.
5. **`day11` PR trigger has no `branches:` filter** → broader than necessary.
6. **Artifact trust boundary** — not currently exploitable here (no privileged consumer), but the pattern must be avoided if added later (see Transfer Challenge).

## 9. Final Security Assessment

- Overall Risk: **Medium-Low for the real repository** (dangerous PR patterns absent; gaps are enforcement/config gaps rather than open exploits). **High for the simulated Workflow B** (deliberately unsafe: `pull_request_target` + privileged checkout + self-hosted + write token + secret).
- Recommended Decision: **Accept with remediation** — add branch protection + required checks; pin actions to full SHAs; add `branches: [main]` to the PR trigger; keep untrusted PR jobs free of secrets and write tokens.
- Outstanding Questions: exact fork-PR token behaviour for this repo; whether any future workflow will consume artifacts across trust levels.
- Next Actions:
  1. Enable branch protection + required status checks on `main`.
  2. Pin all `uses:` to verified full SHAs.
  3. Scope the `day11` PR trigger with `branches: [main]`.
- Reviewer: automated lab review
- Review Date: 2026-11-18

---

## Appendix — Transfer Challenge

Scenario: a high-privilege `workflow_run` workflow downloads an artifact produced by a low-privilege `pull_request` validation workflow and **executes a script inside it**.

- **Attack Path**: external PR → low-privilege validation produces an artifact → high-privilege `workflow_run` workflow downloads and **executes** it → attacker code runs with high privilege.
- **Trust Boundary crossed**: the **Artifact boundary** — low-trust output treated as trusted by a high-trust consumer.
- **Where to place the control**: before downloading/executing the artifact — never execute artifact contents as code; validate provenance; prefer `pull_request` over `workflow_run` for untrusted input; separate privileges.

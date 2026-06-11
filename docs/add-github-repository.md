# Adding a new GitHub repository

This runbook walks through provisioning a **new organisation repository** via Pulumi in `platform-team-admin`, from configuration change to release on GitHub.

There are 2 distict 'Flows'...

1. Validate on push to `main` (CircleCI **preview**)
1. Release on version tag (CircleCI **update** with manual approval).

## Overview

New repositories are declared in [`config/platform_team_values.yaml`](../config/platform_team_values.yaml). Pulumi creates the repo in the **`peplatformidp`** organisation, applies branch protection (signed commits, required PR review), and exports the repo URL.

<!-- Mermaid diagrams sometimes do not render in all IDEs. Here is the flow in plain text for reliability. -->

**Repository Provisioning Flow:**

1. **Edit** `platform_team_values.yaml`  
   ↓  
2. **Create feature branch**  
   ↓  
3. **Commit (signed + Conventional Commits format)**  
   ↓  
4. **Open pull request to `main`**  
   ↓  
5. **PR review and merge**  
   ↓  
6. **CircleCI preview workflow runs**  
   ↓  
7. **Pulumi preview outcome?**  
   - If **No**:  
     a. Fix on branch → new PR → repeat review & merge  
   - If **Yes**:  
     b. Create semantic version tag (`vX.Y.Z`)  
     c. Push tag to GitHub  
     d. CircleCI update workflow  
     e. Pulumi preview runs on tag  
     f. Approve job in CircleCI UI  
     g. Pulumi update applies change  
     h. **New repo live on GitHub!**

## Prerequisites

Complete once per machine / team member:

| Requirement | Notes |
|-------------|-------|
| Git hooks | `./scripts/install-githooks.sh` — enforces [Conventional Commits](https://www.conventionalcommits.org/) |
| SSH commit signing | Commits must be signed (branch protection on all branches) |
| Local secrets (optional) | `.env` + Bitwarden for local `pulumi preview` — see [Getting started](../README.md#getting-started) |
| CircleCI | Project connected; `PLATFORM_ADMIN` context; local runner **Available** — see [circleci.md](circleci.md) |

---

## Step 1 — Declare the repository

Edit [`config/platform_team_values.yaml`](../config/platform_team_values.yaml) and add an entry under `github_repositories`:

```yaml
  - name: platform-observability
    description: 'Observability stack — Prometheus, Grafana, OTEL Collector'
    visibility: public
```

| Field | Required | Values |
|-------|----------|--------|
| `name` | Yes | kebab-case repository name |
| `description` | No | Shown on GitHub |
| `visibility` | No | `private` (default), `public`, or `internal` |

**Optional — validate locally before opening a PR:**

```bash
cd platform-team-admin   # repo root

uv sync --frozen
pulumi login
pulumi stack select dev
pulumi preview
```

You should see a plan to **create** the new `github:Repository` resource. No changes are applied until merge + tag release (or a local `pulumi up`).

---

## Step 2 — Create a feature branch

Always branch from the latest `main`:

```bash
git checkout main
git pull origin main
git checkout -b feat/add-platform-observability-repo
```

**Branch naming:** Branch names must start with an approved prefix (`feat/`, `fix/`, `docs/`, `ci/`, `chore/`, etc.) and use kebab-case for clarity.

**Valid examples:**
- `feat/add-platform-observability-repo`
- `fix/pulumi-platform-demo-apps`
- `docs/add-platform-observability-docs`
- `chore/pulumi-platform-core`
- `ci/add-platform-demo-apps-repo`

**Invalid examples (would be rejected):**
- `feature/add-platform-observability`   ← uses `feature/` instead of `feat/`
- `addPlatformObservabilityRepo`         ← not kebab-case and missing prefix
- `bugfix/pulumi-platform-demo-apps`     ← uses `bugfix/` instead of `fix/`
- `update-platform-observability-repo`   ← missing required prefix
- `main` or `master`                     ← reserved; not for feature branches

---

## Step 3 — Commit and push

Stage only the configuration change (and any related docs):

```bash
git add config/platform_team_values.yaml
git commit -S -m "feat(pulumi): add platform-observability repository"
git push -u origin feat/add-platform-observability-repo
```

| Rule | Detail |
|------|--------|
| **Signed commits** | Use `-S` (or rely on `commit.gpgsign=true`) |
| **Commit message** | Conventional format: `type(scope): description` |
| **Allowed types** | `feat`, `fix`, `docs`, `ci`, `chore`, etc. |

Verify the commit is signed:

```bash
git log -1 --show-signature
```

---

## Step 4 — Open a pull request

You can create a pull request using **either**:

### 1. GitHub Web UI

- Push your feature branch to origin.
- Navigate to the repository on GitHub, and you’ll see a “Compare & pull request” button.
- Click it and use:

  - **Title:** `feat(pulumi): add platform-observability repository`
  - **Description:**
    ```
    ## Summary

    Adds `platform-observability` to `platform_team_values.yaml` for Pulumi provisioning in the peplatformidp organisation.

    ## Test plan

    - [ ] `pulumi preview` shows create of new GitHub repository
    - [ ] After merge: CircleCI **preview** workflow succeeds on `main`
    - [ ] After tag: CircleCI **update** workflow applies change and repo appears on GitHub
    ```

### 2. GitHub CLI

Alternatively, you can use the [`gh`](https://cli.github.com/) CLI to create the PR from your terminal:

```bash
gh pr create \
  --base main \
  --head feat/add-platform-observability-repo \
  --title "feat(pulumi): add platform-observability repository" \
  --body "$(cat <<'EOF'
## Summary

Adds `platform-observability` to `platform_team_values.yaml` for Pulumi provisioning in the peplatformidp organisation.

## Test plan

- [ ] `pulumi preview` shows create of new GitHub repository
- [ ] After merge: CircleCI **preview** workflow succeeds on `main`
- [ ] After tag: CircleCI **update** workflow applies change and repo appears on GitHub
EOF
)"
```

Either method is acceptable as long as you follow the branch naming and PR guidelines above.

---

### What the PR does (and does not) trigger

| Event | CircleCI workflow | Why |
|-------|-------------------|-----|
| PR opened / updated | **None** (with current config) | `preview` filters to branch `main` only |
| **Merge to `main`** | **`preview`** | Push to `main` runs `pulumi preview` |
| **Tag push** `v*.*.*` | **`update`** | Release pipeline with approval gate |

The PR satisfies **branch protection** (signed commits + 1 approving review). CircleCI **preview** runs **after merge**, when the change is on `main`.

---

## Step 5 — Review and merge

1. Request review from a platform team member (or self-review if policy allows).
2. Ensure the PR checks pass (policy / review requirements).
3. **Merge** the PR (squash or merge commit — team preference).

After merge, open [CircleCI Pipelines](https://app.circleci.com/pipelines/github/peplatformidp/platform-team-admin) and confirm:

- Workflow: **`preview`**
- Job: **`pulumi-preview`** — should show the new repository in the plan (create, no apply yet)

If **preview** fails, fix on a new branch and repeat from Step 2.

---

## Step 6 — Release with a version tag

When preview on `main` looks correct, cut a release tag. Tags must match semver: **`v1.2.3`** (three numeric parts; optional pre-release suffix allowed).

```bash
git checkout main
git pull origin main

git tag -a v0.2.0 -m "Release: add platform-observability repository"
git push origin v0.2.0
```

| Tag | Valid? |
|-----|--------|
| `v0.2.0` | Yes |
| `v1.0.0-rc.1` | Yes |
| `v0.2` | No — needs `major.minor.patch` |
| `release-0.2.0` | No — must start with `v` |

---

## Step 7 — Approve the update workflow

Tag push starts the CircleCI **`update`** workflow:

1. **`pulumi-preview`** — dry-run on the tag
2. **`approve-github-changes`** — **manual approval** (click **Approve** in CircleCI UI)
3. **`pulumi-update`** — runs `pulumi update` and **creates the repository**

In CircleCI: open the pipeline for the tag → click **Approve** on the approval job → wait for **`pulumi-update`** to succeed.

---

## Step 8 — Verify on GitHub

```bash
# List org repos (requires gh auth)
gh repo view peplatformidp/platform-observability --web
```

Or browse: `https://github.com/peplatformidp/platform-observability`

Confirm:

- Repository exists with the configured description and visibility
- Branch protection is active (signed commits, PR reviews required)

---

## Quick reference — full command sequence

Replace `platform-observability` and branch/tag names as needed.

```bash
# 1. Edit config/platform_team_values.yaml, then:

git checkout main && git pull origin main
git checkout -b feat/add-platform-observability-repo

git add config/platform_team_values.yaml
git commit -S -m "feat(pulumi): add platform-observability repository"
git push -u origin feat/add-platform-observability-repo

gh pr create --base main --head feat/add-platform-observability-repo \
  --title "feat(pulumi): add platform-observability repository" \
  --body "Adds platform-observability to platform_team_values.yaml."

# 2. Merge PR in GitHub UI → wait for CircleCI preview on main

# 3. Release:
git checkout main && git pull origin main
git tag -a v0.2.0 -m "Release: add platform-observability repository"
git push origin v0.2.0

# 4. Approve update workflow in CircleCI UI → verify repo on GitHub
```

---

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Commit rejected | Conventional commit hook | Fix message format; run `./scripts/install-githooks.sh` |
| Push rejected | Unsigned commit | Use `git commit -S` |
| PR cannot merge | Missing review | Obtain approving review per branch protection |
| No CircleCI pipeline on PR | Expected | Preview runs on **merge to main** only |
| Preview queued forever | Runner offline | Check CircleCI **Runners** → `peplatformidp/local-runner` |
| Preview auth error | Missing context vars | Add `PLATFORM_ADMIN` secrets — see [github.md](github.md) |
| Update workflow not triggered | Wrong tag format | Use `v0.2.0` not `v0.2` |
| Update stuck at approval | Manual gate | Click **Approve** in CircleCI |
| Repo not created after update | Preview showed no changes | Confirm YAML on tag commit matches `main` |

---

## Related documentation

| Guide | Purpose |
|-------|---------|
| [README.md](../README.md) | Project overview and local setup |
| [pulumi.md](pulumi.md) | Pulumi CLI reference |
| [github.md](github.md) | GitHub PAT permissions |
| [circleci.md](circleci.md) | CircleCI CLI and pipeline overview |
| [.circleci/config.yml](../.circleci/config.yml) | Pipeline definition |

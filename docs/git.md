# Git — branches, commits, and release

Daily workflow for this repository: short-lived branches, **signed** Conventional Commits, pull request into `main`.

The [`commit-msg`](../.git-hooks/commit-msg) hook only checks the **first line** of each commit. Branch names are a team convention (not enforced by the hook). Branch protection rejects unsigned commits.

CircleCI triggers and workflows are in [circleci.md](circleci.md). Push vs tag (copy-paste) is in [Release automation](#5-release-automation-push-vs-tag) below. For a new organisation repository, declare it in YAML first: [add-github-repository.md](add-github-repository.md).

## 1. Install the hook (once per clone)

```bash
chmod +x scripts/install-githooks.sh
./scripts/install-githooks.sh
ls -l .git/hooks/commit-msg
```

[`install-githooks.sh`](../scripts/install-githooks.sh) copies `.git-hooks/commit-msg` into `.git/hooks/`. Git does not run hooks from `.git-hooks/` automatically.

## 2. Create a branch

Always start from the latest `main`. Use kebab-case and a Conventional Commits prefix:

```bash
git checkout main
git pull origin main
git checkout -b feat/add-platform-observability-repo
```

| Valid | Invalid |
|-------|---------|
| `feat/add-platform-observability-repo` | `feature/add-platform-observability` (`feature/` is not a type) |
| `fix/pulumi-membership-yaml` | `bugfix/membership` (use `fix/`) |
| `docs/git-workflow` | `update-readme` (missing prefix) |
| `ci/circleci-preview-filters` | `AddNewRepo` (not kebab-case) |

## 3. Commit (copy this template)

Replace the first line from the table below. Do **not** use `--no-verify`. If the hook rejects the message, Git did **not** create the commit — fix the first line and run `git commit` again.

```bash
git add <files>
git commit -S -m "$(cat <<'EOF'
type(scope): short description

Optional body: why, not what. The hook only checks the first line.
EOF
)"
```

One-liner (no body):

```bash
git commit -S -m "feat(pulumi): add platform-observability repository"
```

Confirm the commit is signed:

```bash
git log -1 --show-signature
```

### First-line format

`type(scope)?: description`

- `type` — lowercase, one of: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test`
- `scope` — optional; lowercase letters, numbers, and hyphens only (`pulumi`, `secrets`, `bitwarden`, `github`, `readme`, `circleci`)
- `!` — optional breaking change, for example `feat(api)!:`
- **Space after the colon** is required

### Copy-paste first lines (hook accepts these)

| Type | When | Copy this |
|------|------|-----------|
| `feat` | New behaviour | `feat(pulumi): add platform-observability repository` |
| `fix` | Bug | `fix(secrets): use exact-name Bitwarden lookup` |
| `docs` | Docs only | `docs(readme): add Git commit workflow` |
| `ci` | CircleCI / pipeline | `ci: tighten preview filters on main` |
| `chore` | Housekeeping | `chore: ignore local Pulumi stack config` |
| `refactor` | Same behaviour, clearer code | `refactor(secrets): fetch GitHub item once` |
| `test` | Tests | `test(pulumi): cover repository protect flag` |
| `build` | Deps / toolchain | `build: bump pulumi-github provider` |
| `perf` | Performance | `perf(secrets): list vault items once per run` |
| `style` | Format only | `style: wrap inject_secrets.sh comments` |
| `revert` | Undo | `revert: revert "feat(pulumi): add platform-observability repository"` |

Without scope (also valid): `docs: update installation guide`.

Breaking change: `feat(api)!: require signed tags`.

### Do not paste (hook rejects these)

```
Added the new repo              ← missing type
Feat(pulumi): add repo          ← type must be lowercase
feat:(pulumi) add repo          ← colon in the wrong place
feat:add repo                   ← missing space after the colon
feature(pulumi): add repo       ← "feature" is not an allowed type
fix(Pulumi): correct yaml       ← scope must be lowercase
WIP                             ← not Conventional Commits
```

## 4. Push and open a pull request

Use the same first line as the commit for the PR title:

```bash
git push -u origin feat/add-platform-observability-repo

gh pr create \
  --base main \
  --title "feat(pulumi): add platform-observability repository" \
  --body "$(cat <<'EOF'
## Summary

Adds `platform-observability` to `platform_team_values.yaml`.

## Test plan

- [ ] CircleCI **preview** succeeds after merge to `main`
EOF
)"
```

Merge when reviewed. CircleCI **preview** runs on `main` after merge (not on the PR branch with the current config). See [Release automation](#5-release-automation-push-vs-tag).

## 5. Release automation (push vs tag)

A **push** of commits to `main` only **validates**. A **tag** on that commit **releases** (after you Approve in CircleCI). Pipeline details: [circleci.md](circleci.md).

| Git event | CircleCI workflow | Pulumi |
|-----------|-------------------|--------|
| Merge / push to `main` | **preview** | `pulumi preview` — no apply |
| Tag `vX.Y.Z` on that commit | **update** | Preview → **Approve** → `pulumi update` |
| Push to a feature branch or PR | **None** | Filters are `main` / tags only |

Do not retag or force-push a tag that has already been released. Cut the next version instead (`v0.3.1`, `v0.4.0`).

### Push — validate (copy this)

After the PR is merged, `main` already has the commit. Pull and confirm **preview** in CircleCI:

```bash
git checkout main
git pull origin main

# Optional: confirm you are on the merged commit
git log -1 --oneline
```

Open [CircleCI pipelines](https://app.circleci.com/pipelines/github/peplatformidp/platform-team-admin) for branch **`main`**. Workflow **preview** / job **pulumi-preview** should succeed. Nothing is applied yet.

If preview fails, fix on a new branch ([section 2](#2-create-a-branch)) and merge again. Do not tag until preview on `main` is green.

### Tag — release (copy this)

Tags must match `v<major>.<minor>.<patch>` (optional pre-release suffix). This is what starts workflow **update**.

```bash
git checkout main
git pull origin main

# See the latest tag so you bump the right number
git tag --list 'v*' --sort=-v:refname | head

git tag -a v0.3.0 -m "Release: add platform-observability repository"
git push origin v0.3.0
```

If signing is already configured (same as `git commit -S`), prefer a signed tag:

```bash
git tag -s v0.3.0 -m "Release: add platform-observability repository"
git push origin v0.3.0
```

Optional GitHub Release notes on the same tag:

```bash
gh release create v0.3.0 \
  --verify-tag \
  --title "v0.3.0" \
  --notes "$(cat <<'EOF'
## What's changed

- Add `platform-observability` repository to platform-team-admin IaC
EOF
)"
```

Then in CircleCI, open the pipeline for tag **`v0.3.0`**:

1. Wait for **`pulumi-preview`** on workflow **update**.
2. Click **Approve** on **`approve-github-changes`**.
3. Wait for **`pulumi-update`** — that is the apply.

Until you approve, nothing is applied.

| Tag | Triggers **update**? |
|-----|----------------------|
| `v0.3.0` | Yes |
| `v1.0.0-rc.1` | Yes |
| `v0.3` | No — needs `major.minor.patch` |
| `0.3.0` | No — must start with `v` |
| `release-0.3.0` | No — must start with `v` |

For provisioning a new organisation repository (YAML fields, verify on GitHub), see [add-github-repository.md](add-github-repository.md).

# Git — branches and commits

Daily workflow for this repository: short-lived branches, **signed** Conventional Commits, pull request into `main`.

The [`commit-msg`](../.git-hooks/commit-msg) hook only checks the **first line** of each commit. Branch names are a team convention (not enforced by the hook). Branch protection rejects unsigned commits.

CircleCI triggers and workflows (preview on `main`, update on version tag) are in [circleci.md](circleci.md). To cut a tag and approve the release, see [add-github-repository.md](add-github-repository.md).

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

Merge when reviewed. CircleCI **preview** runs on `main` after merge (not on the PR branch with the current config).

For provisioning a new organisation repository, continue in [add-github-repository.md](add-github-repository.md).

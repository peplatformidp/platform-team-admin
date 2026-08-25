# Adding a new GitHub repository

Declare the repository in YAML. Pulumi then creates it in the **`peplatformidp`** organisation with branch protection (signed commits, required PR review) and exports the repo URL.

Branch, commit, and PR steps are in [git.md](git.md). Push vs tag (CircleCI **preview** / **update**) is in [git.md — Release automation](git.md#5-release-automation-push-vs-tag). Pipeline filters are in [circleci.md](circleci.md).

## Prerequisites

Complete once per machine / team member:

| Requirement | Notes |
|-------------|-------|
| Git hooks | `./scripts/install-githooks.sh` — [git.md](git.md) |
| SSH commit signing | Branch protection requires signed commits |
| Local secrets (optional) | `.env` + Bitwarden for local `pulumi preview` — [Getting started](../README.md#getting-started) |
| CircleCI | `PLATFORM_ADMIN` context; runner **Available** — [circleci.md](circleci.md) |

## Declare the repository

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

**Optional — validate locally before you open a PR:**

```bash
uv sync --frozen
pulumi login
pulumi stack select dev
pulumi preview
```

You should see a plan to **create** the new `github:Repository` resource. Nothing is applied until merge to `main` plus a version tag (or a local `pulumi up`).

## Next steps

1. Branch, commit, PR, merge — [git.md](git.md). Use first line `feat(pulumi): add platform-observability repository`.
2. After merge, confirm CircleCI **preview** on `main` shows the new repository (create, no apply).
3. Tag and approve **update** — [git.md — Release automation](git.md#5-release-automation-push-vs-tag).

## Verify on GitHub

After **update** succeeds:

```bash
gh repo view peplatformidp/platform-observability --web
```

Or browse: `https://github.com/peplatformidp/platform-observability`

Confirm the description, visibility, and branch protection (signed commits, PR reviews).

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Preview shows no create | YAML not on `main` | Merge the PR; confirm the entry in `platform_team_values.yaml` |
| Repo not created after update | Approval skipped, or preview had no changes | Approve in CircleCI; confirm YAML on the tagged commit |
| Preview queued forever | Runner offline | [circleci.md](circleci.md) — `peplatformidp/local-runner` |
| Update workflow not triggered | Wrong tag format | [git.md](git.md#5-release-automation-push-vs-tag) — use `v0.2.0` not `v0.2` |

## Related documentation

| Guide | Purpose |
|-------|---------|
| [git.md](git.md) | Branches, commits, PR, push vs tag |
| [circleci.md](circleci.md) | Pipeline filters, runner, workflows |
| [github.md](github.md) | GitHub PAT permissions |
| [pulumi.md](pulumi.md) | Pulumi CLI reference |

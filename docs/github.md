# GitHub PAT reference


## Cheat sheet

| Item | Value |
|------|-------|
| User account | `peplatformadmin` — creates the PAT (must be org **Owner**) |
| Organisation | `peplatformidp` — resource owner for the PAT |
| Bitwarden item | `GitHub Secrets` |
| Owner field | `pulumi-github-owner` → `peplatformidp` |
| Token field | `pulumi-github-token` → fine-grained PAT |
| Used by | [`pulumi_repo_create.py`](../pulumi_repo_create.py) |

## Permissions

Permissions required for Chapter 1 (`platform-team-admin` Pulumi project):

| Pulumi action | GitHub API | Fine-grained permission |
|---------------|------------|-------------------------|
| Create repositories | `POST /orgs/{org}/repos` | Repository **Administration: Read and write** |
| Branch protection on all branches | `PUT .../branches/{branch}/protection` | Repository **Administration: Read and write** |
| Add/update org members | `PUT /orgs/{org}/memberships/{user}` | Organisation **Members: Read and write** |

GitHub does not offer a separate org token — always create a **personal** fine-grained PAT while logged in as `peplatformadmin`, scoped to the `peplatformidp` org.

## Fine-grained PAT setup

1. Log into GitHub as **`peplatformadmin`** (must be an **Owner** of `peplatformidp`).
2. Go to **Settings → Developer settings → Personal access tokens → Fine-grained tokens**.
3. Click **Generate new token**.

| Field | Value |
|-------|-------|
| Token name | `pulumi-platform-team-admin` |
| Expiration | 90 days (or custom — set a rotation reminder) |
| Description | Pulumi IaC for peplatformidp repos and membership |
| Resource owner | **`peplatformidp`** (the org, not the user) |
| Repository access | **All repositories** (required to create new repos) |

**Organisation permissions**

| Permission | Access |
|------------|--------|
| Members | **Read and write** |

**Repository permissions**

| Permission | Access |
|------------|--------|
| Administration | **Read and write** |
| Metadata | Read-only (included by default) |

4. Click **Generate token** and copy it immediately.
5. If the org requires approval: **peplatformidp → Settings → Personal access tokens** → approve the request.
6. If the org uses SAML SSO: **peplatformidp → Settings → Single sign-on** → **Authorize** the token.

## Store in Bitwarden

Update the `GitHub Secrets` item via [`github_secrets.json`](../secrets-setup/github_secrets.json) and run [`inject_secrets.sh`](../secrets-setup/inject_secrets.sh):

| Field | Value |
|-------|-------|
| `pulumi-github-owner` | `peplatformidp` |
| `pulumi-github-token` | `github_pat_...` |

See [docs/bitwarden.md](bitwarden.md) for Bitwarden CLI usage.

## Verify

```bash
# Token belongs to peplatformadmin
curl -s -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/user | jq .login

# Org is reachable
curl -s -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/orgs/peplatformidp | jq .login

# Membership API (same call Pulumi uses)
curl -s -o /dev/null -w "%{http_code}\n" \
  -X PUT \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role":"admin"}' \
  https://api.github.com/orgs/peplatformidp/memberships/tonydawson1000
```

| HTTP code | Meaning |
|-----------|---------|
| `200` / `204` | Permissions are correct |
| `403` | Not org admin, missing scopes, or SSO not authorized |
| `404` | User not in org yet — invite manually first |

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `"peplatformadmin" is a user` | Owner set to user account, not org | Set `pulumi-github-owner` to `peplatformidp` |
| `403 You must be an admin to add or update an organization membership` | Token user is not org owner, or **Members** permission missing | Create PAT as org owner with **Members: Read and write** |
| `403` on repo create | **Administration** missing or repo access too narrow | Set **Administration: Read and write** and **All repositories** |
| `403` despite correct scopes | SAML SSO not authorized | Authorize token under org SSO settings |
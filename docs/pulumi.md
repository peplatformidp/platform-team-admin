# Pulumi command reference


## Cheat sheet
| Command           | Purpose |
|---------          |---------|
| `pulumi version`  | Check install & version |
| `pulumi login`    | Authenticate with Pulumi Account
| `pulumi stack`    | Show current stack |
| `pulumi preview`  | Dry-run changes |
| `pulumi up`       | Apply changes |

## Working directory

The Pulumi project lives in [`pulumi-repo/`](../pulumi-repo/). Run `pulumi` commands from that directory (after `uv sync` at the repository root):

```bash
cd pulumi-repo
pulumi stack select dev
pulumi preview
```

## Pulumi program

[`pulumi-repo/__main__.py`](../pulumi-repo/__main__.py) manages GitHub organisation resources from [`pulumi-repo/config/platform_team_values.yaml`](../pulumi-repo/config/platform_team_values.yaml). It loads credentials via [`pulumi-repo/bitwarden_secrets.py`](../pulumi-repo/bitwarden_secrets.py), then creates each repo (delete-protected), applies branch protection (signed commits, one review, all branches), and adds organisation members.

Pulumi Cloud project name: **`platform-repo-automation`** (stack **`dev`**).

## Tear down and rebuild
Repositories are delete-protected. 

Unprotect before destroy:

- `pulumi state unprotect 'urn:pulumi:dev::platform-repo-automation::github:index/repository:Repository::platform-team-admin'`

- `pulumi state unprotect 'urn:pulumi:dev::platform-repo-automation::github:index/repository:Repository::platform-core'`

- `pulumi state unprotect 'urn:pulumi:dev::platform-repo-automation::github:index/repository:Repository::platform-demo-apps'`

- `pulumi destroy`

- `pulumi up`

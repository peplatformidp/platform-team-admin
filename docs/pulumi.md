# Pulumi command reference


## Cheat sheet
| Command           | Purpose |
|---------          |---------|
| `pulumi version`  | Check install & version |
| `pulumi login`    | Authenticate with Pulumi Account
| `pulumi stack`    | Show current stack |
| `pulumi preview`  | Dry-run changes |
| `pulumi up`       | Apply changes |

## Pulumi program

[`pulumi_repo_create.py`](../pulumi_repo_create.py) manages GitHub organisation resources from `config/platform_team_values.yaml`. It loads credentials via [`bitwarden_secrets.py`](../bitwarden_secrets.py), then creates each repo (delete-protected), applies branch protection (signed commits, one review, all branches), and adds organisation members. [`__main__.py`](../__main__.py) only imports this file so `pulumi preview` / `up` run it.

## Tear down and rebuild
Repositories are delete-protected. 

Unprotect before destroy:

- `pulumi state unprotect 'urn:pulumi:dev::platform-team-admin::github:index/repository:Repository::platform-team-admin'`

- `pulumi state unprotect 'urn:pulumi:dev::platform-team-admin::github:index/repository:Repository::platform-core'`

- `pulumi state unprotect 'urn:pulumi:dev::platform-team-admin::github:index/repository:Repository::platform-demo-apps'`

- `pulumi destroy`

- `pulumi up`
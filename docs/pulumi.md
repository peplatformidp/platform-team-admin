# Pulumi command reference


## Cheat sheet
| Command           | Purpose |
|---------          |---------|
| `pulumi version`  | Check install & version |
| `pulumi login`    | Authenticate with Pulumi Account
| `pulumi stack`    | Show current stack |
| `pulumi preview`  | Dry-run changes |
| `pulumi up`       | Apply changes |

## Tear down and rebuild
Repositories are delete-protected. 

Unprotect before destroy:

- `pulumi state unprotect 'urn:pulumi:dev::platform-team-admin::github:index/repository:Repository::platform-team-admin'`

- `pulumi state unprotect 'urn:pulumi:dev::platform-team-admin::github:index/repository:Repository::platform-core'`

- `pulumi state unprotect 'urn:pulumi:dev::platform-team-admin::github:index/repository:Repository::platform-demo-apps'`

- `pulumi destroy`

- `pulumi up`
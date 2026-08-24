# Bitwarden command reference


## Cheat sheet
| Command           | Purpose |
|---------          |---------|
| `bw --version`    | Check install & version |

## Scripts

| Command           | Purpose |
|---------          |---------|
| [`secrets-setup/inject_secrets.sh`](../secrets-setup/inject_secrets.sh)    | Read `.json` files in folder and sync 'Secrets' to [Bitwarden](https://vault.bitwarden.eu/#/vault) |

## Python helper

[`bitwarden_secrets.py`](../bitwarden_secrets.py) supplies GitHub credentials to Pulumi. `get_github_credentials()` returns `(owner, token)`. CI uses `PULUMI_GITHUB_OWNER` / `PULUMI_GITHUB_TOKEN`; locally it unlocks Bitwarden, syncs, finds **GitHub Secrets** by exact name, and reads `pulumi-github-owner` and `pulumi-github-token`.

## Custom field types

Each entry under `fields` in [`github_secrets.json`](../secrets-setup/github_secrets.json_example) and [`pulumi_secrets.json`](../secrets-setup/pulumi_secrets.json_example) has a Bitwarden **custom field type**. This only affects how the vault UI displays the value — the CLI and Pulumi still read `.value` the same way.

| `type` | Bitwarden field | When to use |
|--------|-----------------|-------------|
| `0` | Text (shown in the clear) | Non-secrets such as `pulumi-github-owner` |
| `1` | Hidden (masked, like a password) | Tokens and keys such as `pulumi-github-token` and `pulumi-api-key` |
| `2` | Boolean | Not used in this repo |
| `3` | Linked | Not used in this repo |

The item-level `"type": 1` at the top of those JSON files is separate — it means the Bitwarden item is a **Login** cipher, not a field type.
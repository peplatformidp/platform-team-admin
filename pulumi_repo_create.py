"""
pulumi_repo_create.py — GitHub Repository and Team Automation
=============================================================

Creates and manages:
  - GitHub repositories defined in config/platform_team_values.yaml
  - GitHub organisation membership for platform team members
  - Branch protection rules (signed commits, required reviews) on each repo

Usage:
    pulumi preview    # dry-run: shows what would be created/changed
    pulumi up         # apply: create repositories and memberships
    pulumi destroy    # tear down (repositories are delete-protected by default)

Prerequisites:
    pip install pulumi pulumi-github pyyaml

    uv add pulumi
    uv add pulumi-github
    uv add pyyaml

    export PULUMI_ACCESS_TOKEN=<your-token>   # or set via pulumi login

    GitHub credentials are read from Bitwarden (item: "GitHub Secrets"):
      - pulumi-github-owner
      - pulumi-github-token

    Prerequisites:
      - Bitwarden CLI installed and configured (bw config server https://vault.bitwarden.eu)
      - .env with BW_CLIENTID, BW_CLIENTSECRET, BW_PASSWORD
      - secrets-setup/inject_secrets.sh run to sync github_secrets.json into Bitwarden

Configuration:
    All repositories and team members are defined in config/platform_team_values.yaml.
    Edit that file and re-run `pulumi up` to add or update resources.
"""

from __future__ import annotations

import yaml
import pulumi
import pulumi_github as github
from pulumi import ResourceOptions, export

from bitwarden_secrets import get_github_credentials

# ── Load configuration ────────────────────────────────────────────────────────
CONFIG_FILE = "config/platform_team_values.yaml"

with open(CONFIG_FILE) as f:
    data = yaml.safe_load(f)

# ── GitHub provider ───────────────────────────────────────────────────────────
# Credentials are fetched from Bitwarden (GitHub Secrets secure note).
github_owner, github_token = get_github_credentials()

github_provider = github.Provider(
    "platform-github-provider",
    token=github_token,
    owner=github_owner,
)

# ── Create GitHub repositories ────────────────────────────────────────────────
repositories: dict[str, github.Repository] = {}

for repo_def in data.get("github_repositories", []):
    repo_name: str = repo_def["name"]
    repo_description: str = repo_def.get("description", "")
    visibility: str = repo_def.get("visibility", "private")

    repo = github.Repository(
        repo_name,
        name=repo_name,
        description=repo_description,
        visibility=visibility,
        # Delete protection: prevents `pulumi destroy` from removing repositories.
        # Remove this flag only when intentionally decommissioning a repo.
        allow_auto_merge=False,
        delete_branch_on_merge=False,
        opts=ResourceOptions(
            provider=github_provider,
            protect=True,  # prevents accidental deletion via pulumi destroy
        ),
    )
    repositories[repo_name] = repo

    # ── Branch protection: enforce signed commits on main ─────────────────────
    # Every commit to main must be GPG- or SSH-signed by the committing developer.
    # This satisfies code-commit signing requirements in regulated environments
    # (SOC 2, ISO 27001) and provides a cryptographic audit trail.
    github.BranchProtection(
        f"{repo_name}-main-branch-protection",
        repository_id=repo.node_id,
        pattern="main",
        enforce_admins=True,
        require_signed_commits=True,
        required_pull_request_reviews=[
            github.BranchProtectionRequiredPullRequestReviewArgs(
                dismiss_stale_reviews=True,
                required_approving_review_count=1,
            )
        ],
        opts=ResourceOptions(
            provider=github_provider,
            depends_on=[repo],
        ),
    )

    # Export the repository name for use by other Pulumi stacks
    export(f"{repo_name}_repo_name", repo.name)
    export(f"{repo_name}_repo_url", repo.html_url)


# ── Add GitHub organisation members ──────────────────────────────────────────
# Team members are added to the organisation with the role defined in config.
# Note: you cannot automate management of the organisation owner.
# Add a second GitHub account (e.g. youremail+peh-team-member@gmail.com)
# to test member onboarding as described in Chapter 1.

for member_def in data.get("github_organisation_members", []):
    username: str = member_def["github-username"]
    role: str = member_def.get("github-role", "member")

    github.Membership(
        f"github-membership-{username}",
        username=username,
        role=role,
        opts=ResourceOptions(provider=github_provider),
    )

    pulumi.log.info(f"Managing GitHub membership: {username} ({role})")

    # Export the managed GitHub user and their role for use by other Pulumi stacks
    export(f"github_member_{username}_username", username)
    export(f"github_member_{username}_role", role)

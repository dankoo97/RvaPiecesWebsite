# Branch rulesets

Copies of the rulesets applied to this repo. GitHub doesn't read these files: they're a record,
and can be used to recreate or update the live rulesets.

| File | Live ruleset | Protects |
|---|---|---|
| `main-protection.json` | `ProtectPushToMain` (id 11789823) | `main`: changes only through PRs, code-owner approval, `source-branch` check, no force-push or deletion |
| `dev-protection.json` | `ProtectDev` (id 27327481) | `dev`: can't be deleted |

Both name their branch explicitly rather than using `~DEFAULT_BRANCH`, because the default
branch is `dev`.

```sh
# Update a live ruleset from its file
gh api -X PUT repos/dankoo97/RvaPiecesWebsite/rulesets/<id> --input .github/rulesets/<file>.json
# Create one from scratch
gh api -X POST repos/dankoo97/RvaPiecesWebsite/rulesets --input .github/rulesets/<file>.json
```

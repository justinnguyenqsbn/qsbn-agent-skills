---
description: Sync a feature's epic and stories to Azure DevOps
argument-hint: <feature | feature-id>
---
Check if `ado` or `azure-devops` configured. If not, tell user we need to configure `Azure DevOps` prior to continue, then invoke `qsbn-setup` skill.

After the setup is done, or the configuration is found, invoke the `qsbn-sync-to-tracker` skill, with `$ARGUMENTS` as the feature identifier and `--target azure-devops` fixed, regardless of whatever `tracker` is set in `.qsbn/config.toml`.
